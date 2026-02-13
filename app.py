import tkinter as tk
from tkinter import messagebox
import sqlite3
from pathlib import Path
from datetime import date
try:
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MPL = True
except Exception:
    HAS_MPL = False

# ------------------ DB SETUP (same idea as your Streamlit code) ------------------
# ensure the sqlite file lives next to this script (robust on different cwd)
DB_PATH = str(Path(__file__).parent / "finance_app.db")

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    """)
    # transactions table to store user spendings
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT,
            note TEXT,
            tdate TEXT NOT NULL,
            FOREIGN KEY(username) REFERENCES users(username)
        )
    """)
    conn.commit()
    conn.close()

def user_exists(username: str) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    return row is not None

def create_user(username: str, password: str):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users(username, password) VALUES(?, ?)", (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # username already exists
        return False
    finally:
        conn.close()

def validate_login(username: str, password: str) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE username = ? AND password = ?", (username, password))
    row = cur.fetchone()
    conn.close()
    return row is not None


def add_transaction(username: str, amount: float, category: str = None, note: str = None, tdate: str = None) -> bool:
    if tdate is None:
        tdate = date.today().isoformat()
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO transactions(username, amount, category, note, tdate) VALUES(?,?,?,?,?)",
                    (username, float(amount), category, note, tdate))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def get_transactions_for_user(username: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, amount, category, note, tdate FROM transactions WHERE username = ? ORDER BY tdate DESC", (username,))
    rows = cur.fetchall()
    conn.close()
    return rows


# ------------------ TKINTER APP ------------------
class FinanceCopilotApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Finance Copilot")
        self.geometry("420x560")
        self.resizable(False, False)

        init_db()

        self.current_user = None
        self.flash_success = ""   # success msg on login page after signup

        container = tk.Frame(self, bg="#f2f2f2")
        container.pack(fill="both", expand=True)

        self.frames = {}
        for F in (LoginPage, CreateAccountPage, DashboardPage):
            frame = F(container, self)
            self.frames[F.__name__] = frame
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.show_frame("LoginPage")

    def show_frame(self, name: str):
        frame = self.frames[name]
        frame.on_show()
        frame.tkraise()


# ------------------ UI COMPONENT: "Card" ------------------
def make_card(parent, width=340, height=440):
    card = tk.Frame(parent, bg="white", bd=0, highlightthickness=0)
    # center the card
    card.place(relx=0.5, rely=0.5, anchor="center", width=width, height=height)
    return card


# ------------------ LOGIN PAGE ------------------
class LoginPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f2f2f2")
        self.controller = controller

        card = make_card(self)
        tk.Label(card, text="Login", font=("Arial", 18), bg="white").pack(pady=10)

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()

        tk.Entry(card, textvariable=self.username_var).pack(pady=5)
        tk.Entry(card, textvariable=self.password_var, show="*").pack(pady=5)

        tk.Button(card, text="Login", command=self.attempt_login).pack(pady=10)
        tk.Button(card, text="Create Account", command=lambda: controller.show_frame("CreateAccountPage")).pack()

    def attempt_login(self):
        u = self.username_var.get().strip()
        p = self.password_var.get().strip()
        if validate_login(u, p):
            self.controller.current_user = u
            self.controller.show_frame("DashboardPage")
        else:
            messagebox.showerror("Login failed", "Invalid credentials")

    def on_show(self):
        pass


class CreateAccountPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f2f2f2")
        self.controller = controller

        card = make_card(self)
        tk.Label(card, text="Create Account", font=("Arial", 18), bg="white").pack(pady=10)

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()

        tk.Entry(card, textvariable=self.username_var).pack(pady=5)
        tk.Entry(card, textvariable=self.password_var, show="*").pack(pady=5)

        tk.Button(card, text="Create", command=self.create_account).pack(pady=10)
        tk.Button(card, text="Back to Login", command=lambda: controller.show_frame("LoginPage")).pack()

    def create_account(self):
        u = self.username_var.get().strip()
        p = self.password_var.get().strip()
        if not u or not p:
            messagebox.showwarning("Invalid", "Username and password required")
            return
        # try creating user (create_user now returns False if username exists)
        ok = create_user(u, p)
        if not ok:
            messagebox.showwarning("Exists", "User already exists")
            return
        self.controller.flash_success = "Account created, please login."
        messagebox.showinfo("Success", "Account created. You can now login.")
        self.controller.show_frame("LoginPage")

    def on_show(self):
        pass


class DashboardPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f2f2f2")
        self.controller = controller

        card = make_card(self)
        self.welcome_label = tk.Label(card, text="", font=("Arial", 16), bg="white")
        self.welcome_label.pack(pady=20)

        tk.Button(card, text="Logout", command=self.logout).pack(pady=10)

    def on_show(self):
        user = self.controller.current_user or "(not logged in)"
        self.welcome_label.config(text=f"Welcome, {user}")

    def logout(self):
        self.controller.current_user = None
        self.controller.show_frame("LoginPage")


if __name__ == "__main__":
    app = FinanceCopilotApp()
    app.mainloop()
