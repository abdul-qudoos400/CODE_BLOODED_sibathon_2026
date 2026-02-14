import sqlite3
from pathlib import Path
from typing import List, Tuple, Optional

DB_PATH = Path(__file__).parent / "finance_app.db"

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    with get_conn() as conn:
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            amount REAL,
            category TEXT,
            note TEXT,
            tdate TEXT
        )
        """)
        conn.commit()

def ensure_user(username: str, password: str) -> None:
    """Create user if not exists (case-insensitive uniqueness)."""
    username_clean = username.strip()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT username FROM users WHERE LOWER(username)=LOWER(?)", (username_clean,))
        row = cur.fetchone()
        if row:
            return
        cur.execute("INSERT INTO users(username, password) VALUES (?, ?)", (username_clean, password))
        conn.commit()

def validate_login(username: str, password: str) -> Optional[str]:
    """Return canonical username from DB if login OK, else None."""
    u = username.strip()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT username FROM users WHERE LOWER(username)=LOWER(?) AND password=?",
            (u, password),
        )
        row = cur.fetchone()
        return row[0] if row else None

def add_transaction(username: str, amount: float, category: str, note: str, tdate: str) -> None:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO transactions(username, amount, category, note, tdate) VALUES(?,?,?,?,?)",
            (username, float(amount), category, note, tdate),
        )
        conn.commit()

def get_transactions(username: str) -> List[Tuple]:
    """Returns list of (id, amount, category, note, tdate) for username (case-insensitive)."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, amount, category, note, tdate
            FROM transactions
            WHERE LOWER(username)=LOWER(?)
            ORDER BY tdate DESC, id DESC
            """,
            (username,),
        )
        return cur.fetchall()

def count_transactions(username: str) -> int:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM transactions WHERE LOWER(username)=LOWER(?)", (username,))
        return int(cur.fetchone()[0])