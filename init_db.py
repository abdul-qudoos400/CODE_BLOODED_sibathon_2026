import sqlite3
from pathlib import Path

DB_PATH = Path("db/finance.db")

schema = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  name TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS categories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  UNIQUE(user_id, name)
);

CREATE TABLE IF NOT EXISTS transactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  amount_minor INTEGER NOT NULL,
  txn_type TEXT NOT NULL,     -- expense/income
  txn_date TEXT NOT NULL,     -- ISO date/time
  description TEXT,
  category_id INTEGER,
  category_source TEXT NOT NULL DEFAULT 'none', -- none/manual/ml
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_tx_user_date ON transactions(user_id, txn_date);
CREATE INDEX IF NOT EXISTS idx_tx_user_cat ON transactions(user_id, category_id);
"""

def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(schema)
    conn.close()
    print("✅ Created DB at:", DB_PATH.resolve())

if __name__ == "__main__":
    main()
