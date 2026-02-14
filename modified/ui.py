import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import threading  # ✅ ADDED

from savings_coach import recommend, UserProfile

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from db import validate_login, ensure_user, add_transaction, get_transactions
from charts import totals_by_category, totals_by_month, totals_by_week
from insights_adapter import run_insights


# ----------------------------
# Theme
# ----------------------------
COLORS = {
    "bg": "#F6F7FB",
    "card": "#FFFFFF",
    "text": "#111827",
    "muted": "#6B7280",
    "accent": "#2563EB",
    "accent_hover": "#1D4ED8",
    "border": "#E5E7EB",
    "danger": "#EF4444",
    "danger_hover": "#DC2626",

    # New login palette
    "login_bg": "#E9E2D6",
    "login_card": "#FFFFFF",
    "blob_purple": "#6B3E63",
    "blob_pink": "#F29CA3",
    "blob_yellow": "#E9D36A",
    "underline": "#C9CDD6",
    "cta": "#7A4A6E",
    "cta_hover": "#6A3E63",
}

FONTS = {
    "h1": ("Segoe UI", 28, "bold"),
    "h2": ("Segoe UI", 18, "bold"),
    "h3": ("Segoe UI", 14, "bold"),
    "body": ("Segoe UI", 11),
    "small": ("Segoe UI", 10),
}


def center_window(win: tk.Tk, w=380, h=680):
    win.update_idletasks()
    x = (win.winfo_screenwidth() // 2) - (w // 2)
    y = (win.winfo_screenheight() // 2) - (h // 2)
    win.geometry(f"{w}x{h}+{x}+{y}")


class RoundedButton(tk.Canvas):
    """Simple rounded button with hover."""
    def __init__(
        self, master, text, command=None,
        w=140, h=44, radius=18,
        bg=COLORS["card"], fg=COLORS["text"],
        hover_bg="#F3F4F6", font=FONTS["body"]
    ):
        super().__init__(master, width=w, height=h, highlightthickness=0, bg=master["bg"])
        self.command = command
        self.w = w
        self.h = h
        self.radius = radius
        self.bg_color = bg
        self.hover_bg = hover_bg
        self.fg_color = fg
        self.font = font
        self.text = text
        self._draw(bg)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _round_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1+r, y1,  x2-r, y1,  x2, y1,  x2, y1+r,
            x2, y2-r,  x2, y2,  x2-r, y2,  x1+r, y2,
            x1, y2,  x1, y2-r,  x1, y1+r,  x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def _draw(self, fill):
        self.delete("all")
        self._round_rect(2, 2, self.w-2, self.h-2, self.radius, fill=fill, outline=fill)
        self.create_text(self.w//2, self.h//2, text=self.text, fill=self.fg_color, font=self.font)

    def _on_click(self, _):
        if self.command:
            self.command()

    def _on_enter(self, _):
        self._draw(self.hover_bg)

    def _on_leave(self, _):
        self._draw(self.bg_color)


def make_card(master, width=330, height=260, padx=18, pady=18):
    card = tk.Frame(master, bg=COLORS["card"], highlightthickness=1, highlightbackground=COLORS["border"])
    card.configure(width=width, height=height)
    card.pack_propagate(False)
    inner = tk.Frame(card, bg=COLORS["card"])
    inner.pack(fill="both", expand=True, padx=padx, pady=pady)
    return card, inner


# ----------------------------
# Main App
# ----------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Finance Copilot")
        self.configure(bg=COLORS["bg"])
        center_window(self, 380, 680)

        self.current_user = None

        container = tk.Frame(self, bg=COLORS["bg"])
        container.pack(fill="both", expand=True)

        self.frames = {}
        for F in (LoginPage, SignupPage, DashboardPage, AddTxnPage, HistoryPage, GraphsPage):
            frame = F(container, self)
            self.frames[F.__name__] = frame
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.show_frame("LoginPage")

    def show_frame(self, name: str):
        frame = self.frames[name]
        frame.tkraise()
        if hasattr(frame, "on_show"):
            frame.on_show()


# ----------------------------
# Pages
# ----------------------------
class LoginPage(tk.Frame):
    def __init__(self, parent, app: App):
        super().__init__(parent, bg=COLORS["login_bg"])
        self.app = app

        phone = tk.Frame(self, bg=COLORS["login_card"], highlightthickness=0)
        phone.place(relx=0.5, rely=0.5, anchor="center", width=330, height=610)

        back = tk.Label(phone, text="‹", bg=COLORS["login_card"], fg=COLORS["muted"], font=("Segoe UI", 18, "bold"))
        back.place(x=18, y=14)

        blob = tk.Canvas(phone, width=330, height=210, bg=COLORS["login_card"], highlightthickness=0)
        blob.place(x=0, y=0)

        blob.create_oval(-60, -70, 170, 160, fill=COLORS["blob_pink"], outline=COLORS["blob_pink"])
        blob.create_oval(200, 40, 410, 250, fill=COLORS["blob_yellow"], outline=COLORS["blob_yellow"])
        blob.create_oval(60, -10, 310, 210, fill=COLORS["blob_purple"], outline=COLORS["blob_purple"])
        blob.create_text(60, 110, text="Welcome\nBack", fill="white",
                         font=("Segoe UI", 18, "bold"), anchor="w")

        form = tk.Frame(phone, bg=COLORS["login_card"])
        form.place(x=28, y=230, width=274)

        tk.Label(form, text="Username", bg=COLORS["login_card"], fg=COLORS["muted"], font=("Segoe UI", 9)).pack(anchor="w")
        self.e_user = tk.Entry(form, bd=0, bg=COLORS["login_card"], fg=COLORS["text"], font=("Segoe UI", 11))
        self.e_user.pack(fill="x", pady=(4, 2))
        tk.Frame(form, bg=COLORS["underline"], height=1).pack(fill="x", pady=(0, 18))

        tk.Label(form, text="Password", bg=COLORS["login_card"], fg=COLORS["muted"], font=("Segoe UI", 9)).pack(anchor="w")
        self.e_pass = tk.Entry(form, bd=0, show="•", bg=COLORS["login_card"], fg=COLORS["text"], font=("Segoe UI", 11))
        self.e_pass.pack(fill="x", pady=(4, 2))
        tk.Frame(form, bg=COLORS["underline"], height=1).pack(fill="x", pady=(0, 18))

        sign_row = tk.Frame(phone, bg=COLORS["login_card"])
        sign_row.place(x=28, y=385, width=274, height=70)

        tk.Label(sign_row, text="Sign in", bg=COLORS["login_card"], fg=COLORS["text"],
                 font=("Segoe UI", 14, "bold")).pack(side="left", anchor="s")

        self.arrow_btn = tk.Canvas(sign_row, width=56, height=56, bg=COLORS["login_card"], highlightthickness=0)
        self.arrow_btn.pack(side="right")
        self._draw_circle_button(self.arrow_btn, COLORS["cta"])
        self.arrow_btn.configure(cursor="hand2")
        self.arrow_btn.bind("<Button-1>", lambda e: self.do_login())
        self.arrow_btn.bind("<Enter>", lambda e: self._draw_circle_button(self.arrow_btn, COLORS["cta_hover"]))
        self.arrow_btn.bind("<Leave>", lambda e: self._draw_circle_button(self.arrow_btn, COLORS["cta"]))

        bottom = tk.Frame(phone, bg=COLORS["login_card"])
        bottom.place(x=28, y=540, width=274)

        link1 = tk.Label(bottom, text="Sign up", bg=COLORS["login_card"], fg=COLORS["muted"],
                         font=("Segoe UI", 9, "underline"), cursor="hand2")
        link1.pack(side="left")
        link1.bind("<Button-1>", lambda e: self.app.show_frame("SignupPage"))

        link2 = tk.Label(bottom, text="Forgot Password", bg=COLORS["login_card"], fg=COLORS["muted"],
                         font=("Segoe UI", 9, "underline"), cursor="hand2")
        link2.pack(side="right")
        link2.bind("<Button-1>", lambda e: messagebox.showinfo("Forgot Password", "Later: implement password reset."))

    def _draw_circle_button(self, canvas: tk.Canvas, color: str):
        canvas.delete("all")
        canvas.create_oval(4, 4, 52, 52, fill=color, outline=color)
        canvas.create_text(28, 28, text="→", fill="white", font=("Segoe UI", 14, "bold"))

    def do_login(self):
        u = self.e_user.get().strip()
        p = self.e_pass.get().strip()
        canonical = validate_login(u, p)
        if not canonical:
            messagebox.showerror("Login Failed", "Invalid username or password.")
            return
        self.app.current_user = canonical
        self.app.show_frame("DashboardPage")


class SignupPage(tk.Frame):
    def __init__(self, parent, app: App):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app

        tk.Label(self, text="", bg=COLORS["bg"]).pack(pady=22)
        tk.Label(self, text="Create Account", bg=COLORS["bg"], fg=COLORS["text"], font=FONTS["h2"]).pack(pady=6)
        tk.Label(self, text="Sign up to start tracking", bg=COLORS["bg"], fg=COLORS["muted"], font=FONTS["body"]).pack(pady=2)

        card, inner = make_card(self, height=320)
        card.pack(pady=20)

        tk.Label(inner, text="Username", bg=COLORS["card"], fg=COLORS["muted"], font=FONTS["small"]).pack(anchor="w")
        self.e_user = ttk.Entry(inner)
        self.e_user.pack(fill="x", pady=(6, 14))

        tk.Label(inner, text="Password", bg=COLORS["card"], fg=COLORS["muted"], font=FONTS["small"]).pack(anchor="w")
        self.e_pass = ttk.Entry(inner, show="•")
        self.e_pass.pack(fill="x", pady=(6, 14))

        tk.Label(inner, text="Confirm Password", bg=COLORS["card"], fg=COLORS["muted"], font=FONTS["small"]).pack(anchor="w")
        self.e_confirm = ttk.Entry(inner, show="•")
        self.e_confirm.pack(fill="x", pady=(6, 12))

        RoundedButton(
            inner, "Sign Up",
            command=self.do_signup,
            w=290, h=44,
            bg=COLORS["accent"], fg="white",
            hover_bg=COLORS["accent_hover"]
        ).pack(pady=8)

        link = tk.Label(self, text="Already have an account? Login",
                        bg=COLORS["bg"], fg=COLORS["accent"], font=FONTS["body"], cursor="hand2")
        link.pack(pady=12)
        link.bind("<Button-1>", lambda e: self.app.show_frame("LoginPage"))

        style = ttk.Style()
        style.configure("TEntry", padding=10)

    def do_signup(self):
        u = self.e_user.get().strip()
        p = self.e_pass.get().strip()
        c = self.e_confirm.get().strip()
        if not u or not p:
            messagebox.showerror("Error", "Username and password required.")
            return
        if p != c:
            messagebox.showerror("Error", "Passwords do not match.")
            return
        try:
            ensure_user(u, p)
        except Exception:
            messagebox.showerror("Error", "User already exists.")
            return
        messagebox.showinfo("Success", "Account created. Please login.")
        self.app.show_frame("LoginPage")


class DashboardPage(tk.Frame):
    def __init__(self, parent, app: App):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app

        top = tk.Frame(self, bg=COLORS["bg"])
        top.pack(fill="x", padx=18, pady=(16, 8))

        self.lbl_greet = tk.Label(top, text="Good morning", bg=COLORS["bg"], fg=COLORS["muted"], font=FONTS["small"])
        self.lbl_greet.pack(anchor="w")

        self.lbl_name = tk.Label(top, text="USER", bg=COLORS["bg"], fg=COLORS["text"], font=FONTS["h1"])
        self.lbl_name.pack(anchor="w", pady=(2, 0))

        tk.Label(top, text="Personal Finance Copilot", bg=COLORS["bg"], fg=COLORS["muted"], font=FONTS["body"]).pack(anchor="w")

        RoundedButton(
            top, "🔍",
            command=lambda: messagebox.showinfo("Search", "Later: connect search to history."),
            w=44, h=44,
            bg=COLORS["card"], fg=COLORS["text"],
            hover_bg="#F3F4F6"
        ).pack(side="right")

        section = tk.Frame(self, bg=COLORS["bg"])
        section.pack(fill="x", padx=18, pady=(20, 10))

        row = tk.Frame(section, bg=COLORS["bg"])
        row.pack(fill="x")

        RoundedButton(row, "📊  Graphs", w=105, h=42, command=lambda: self.app.show_frame("GraphsPage")).pack(side="left", padx=(0, 10))
        RoundedButton(row, "➕  Add Data", w=120, h=42, command=lambda: self.app.show_frame("AddTxnPage")).pack(side="left", padx=(0, 10))
        RoundedButton(row, "🧾  History", w=105, h=42, command=lambda: self.app.show_frame("HistoryPage")).pack(side="left")

        bottom = tk.Frame(self, bg=COLORS["bg"])
        bottom.pack(side="bottom", fill="x", padx=18, pady=18)

        RoundedButton(
            bottom, "Logout",
            command=self.logout,
            w=330, h=46,
            bg=COLORS["danger"], fg="white",
            hover_bg=COLORS["danger_hover"]
        ).pack()

    def on_show(self):
        user = self.app.current_user or "USER"
        self.lbl_name.config(text=user.upper())

    def logout(self):
        self.app.current_user = None
        self.app.show_frame("LoginPage")


class AddTxnPage(tk.Frame):
    def __init__(self, parent, app: App):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app

        top = tk.Frame(self, bg=COLORS["bg"])
        top.pack(fill="x", padx=18, pady=(16, 8))
        RoundedButton(top, "←", command=lambda: self.app.show_frame("DashboardPage"), w=44, h=44).pack(side="left")
        tk.Label(top, text="Add Transaction", bg=COLORS["bg"], fg=COLORS["text"], font=FONTS["h2"]).pack(side="left", padx=10)

        card, inner = make_card(self, height=360)
        card.pack(pady=18)

        def lab(text):
            tk.Label(inner, text=text, bg=COLORS["card"], fg=COLORS["muted"], font=FONTS["small"]).pack(anchor="w")

        lab("Amount")
        self.e_amount = ttk.Entry(inner)
        self.e_amount.pack(fill="x", pady=(6, 14))

        lab("Category (Food, Bills, Transport...)")
        self.e_cat = ttk.Entry(inner)
        self.e_cat.pack(fill="x", pady=(6, 14))

        lab("Note")
        self.e_note = ttk.Entry(inner)
        self.e_note.pack(fill="x", pady=(6, 14))

        lab("Date (YYYY-MM-DD)")
        self.e_date = ttk.Entry(inner)
        self.e_date.pack(fill="x", pady=(6, 12))

        RoundedButton(
            inner, "Save",
            command=self.save,
            w=290, h=44,
            bg=COLORS["accent"], fg="white",
            hover_bg=COLORS["accent_hover"]
        ).pack(pady=10)

    def save(self):
        if not self.app.current_user:
            messagebox.showerror("Error", "Please login again.")
            return

        try:
            amount = float(self.e_amount.get().strip())
        except Exception:
            messagebox.showerror("Invalid", "Amount must be a number.")
            return

        cat = self.e_cat.get().strip() or "Other"
        note = self.e_note.get().strip()
        tdate = self.e_date.get().strip()

        try:
            datetime.strptime(tdate, "%Y-%m-%d")
        except Exception:
            messagebox.showerror("Invalid", "Date must be YYYY-MM-DD")
            return

        add_transaction(self.app.current_user, amount, cat, note, tdate)
        messagebox.showinfo("Saved", "Transaction added.")
        self.app.show_frame("DashboardPage")


class HistoryPage(tk.Frame):
    def __init__(self, parent, app: App):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app

        top = tk.Frame(self, bg=COLORS["bg"])
        top.pack(fill="x", padx=18, pady=(16, 8))
        RoundedButton(top, "←", command=lambda: self.app.show_frame("DashboardPage"), w=44, h=44).pack(side="left")
        tk.Label(top, text="History", bg=COLORS["bg"], fg=COLORS["text"], font=FONTS["h2"]).pack(side="left", padx=10)

        self.list_wrap = tk.Frame(self, bg=COLORS["bg"])
        self.list_wrap.pack(fill="both", expand=True, padx=18, pady=10)

        self.canvas = tk.Canvas(self.list_wrap, bg=COLORS["bg"], highlightthickness=0)
        self.scroll = ttk.Scrollbar(self.list_wrap, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=COLORS["bg"])

        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scroll.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scroll.pack(side="right", fill="y")

    def on_show(self):
        for w in self.inner.winfo_children():
            w.destroy()

        if not self.app.current_user:
            return

        rows = get_transactions(self.app.current_user)
        if not rows:
            tk.Label(self.inner, text="No transactions yet.", bg=COLORS["bg"], fg=COLORS["muted"]).pack(pady=20)
            return

        for _id, amount, category, note, tdate in rows:
            card = tk.Frame(self.inner, bg=COLORS["card"], highlightthickness=1, highlightbackground=COLORS["border"])
            card.pack(fill="x", pady=8)

            left = tk.Frame(card, bg=COLORS["card"])
            left.pack(side="left", padx=12, pady=10, fill="x", expand=True)

            tk.Label(left, text=f"{category}", bg=COLORS["card"], fg=COLORS["text"], font=FONTS["h3"]).pack(anchor="w")
            tk.Label(left, text=f"{note}" if note else "—", bg=COLORS["card"], fg=COLORS["muted"], font=FONTS["small"]).pack(anchor="w", pady=(2, 0))
            tk.Label(left, text=f"{tdate}", bg=COLORS["card"], fg=COLORS["muted"], font=FONTS["small"]).pack(anchor="w", pady=(2, 0))

            right = tk.Frame(card, bg=COLORS["card"])
            right.pack(side="right", padx=12, pady=10)

            tk.Label(right, text=f"PKR {float(amount):,.0f}", bg=COLORS["card"], fg=COLORS["accent"], font=FONTS["h3"]).pack(anchor="e")


class GraphsPage(tk.Frame):
    def __init__(self, parent, app: App):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self._canvases = []

        top = tk.Frame(self, bg=COLORS["bg"])
        top.pack(fill="x", padx=18, pady=(16, 8))
        RoundedButton(top, "←", command=lambda: self.app.show_frame("DashboardPage"), w=44, h=44).pack(side="left")
        tk.Label(top, text="Graphs", bg=COLORS["bg"], fg=COLORS["text"], font=FONTS["h2"]).pack(side="left", padx=10)

        RoundedButton(top, "🧠 Insights", command=self.show_insights, w=110, h=44).pack(side="right")
        RoundedButton(top, "💡 Coach", command=self.show_coach, w=100, h=44).pack(side="right", padx=(0, 10))

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=18, pady=12)

        self.tab_pie = tk.Frame(self.notebook, bg=COLORS["bg"])
        self.tab_month = tk.Frame(self.notebook, bg=COLORS["bg"])
        self.tab_week = tk.Frame(self.notebook, bg=COLORS["bg"])

        self.notebook.add(self.tab_pie, text="Pie")
        self.notebook.add(self.tab_month, text="Monthly")
        self.notebook.add(self.tab_week, text="Weekly")

    def _clear_tab(self, tab):
        for w in tab.winfo_children():
            w.destroy()

    def _draw_pie(self, tab, data):
        self._clear_tab(tab)
        if not data:
            tk.Label(tab, text="No data for this user.", bg=COLORS["bg"], fg=COLORS["muted"]).pack(pady=30)
            return

        labels = list(data.keys())
        sizes = list(data.values())

        fig = Figure(figsize=(3.2, 3.2), dpi=110)
        ax = fig.add_subplot(111)
        ax.pie(sizes, labels=labels, autopct="%1.1f%%")
        ax.set_title("Spending by Category")

        canvas = FigureCanvasTkAgg(fig, master=tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self._canvases.append(canvas)

    def _draw_bar(self, tab, data, title, xlabel):
        self._clear_tab(tab)
        if not data:
            tk.Label(tab, text="No data for this user.", bg=COLORS["bg"], fg=COLORS["muted"]).pack(pady=30)
            return

        keys = list(data.keys())
        vals = list(data.values())

        fig = Figure(figsize=(3.2, 3.2), dpi=110)
        ax = fig.add_subplot(111)
        ax.bar(keys, vals)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Amount")
        ax.tick_params(axis="x", rotation=35)

        canvas = FigureCanvasTkAgg(fig, master=tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self._canvases.append(canvas)

    def on_show(self):
        if not self.app.current_user:
            return
        rows = get_transactions(self.app.current_user)

        cat = totals_by_category(rows)
        mon = totals_by_month(rows)
        wek = totals_by_week(rows)

        self._draw_pie(self.tab_pie, cat)
        self._draw_bar(self.tab_month, mon, "Monthly Spending", "YYYY-MM")
        self._draw_bar(self.tab_week, wek, "Weekly Spending", "YYYY-W##")

    def show_insights(self):
        if not self.app.current_user:
            return
        rows = get_transactions(self.app.current_user)
        text = run_insights(rows)

        win = tk.Toplevel(self)
        win.title("Insights")
        win.geometry("720x520")
        win.configure(bg=COLORS["bg"])

        card, inner = make_card(win, width=700, height=500, padx=14, pady=14)
        card.pack(padx=10, pady=10)

        t = tk.Text(inner, wrap="word", font=("Segoe UI", 10))
        t.pack(fill="both", expand=True)
        t.insert("1.0", text)
        t.config(state="disabled")

    # ----------------------------
    # ✅ COACH: threaded (NO FREEZE)
    # ----------------------------
    def show_coach(self):
        if not self.app.current_user:
            return

        win = tk.Toplevel(self)
        win.title("Savings Coach")
        win.geometry("720x520")
        win.configure(bg=COLORS["bg"])

        card, inner = make_card(win, width=700, height=500, padx=14, pady=14)
        card.pack(padx=10, pady=10)

        controls = tk.Frame(inner, bg=COLORS["card"])
        controls.pack(fill="x", pady=(0, 10))

        tk.Label(
            controls,
            text="Enter your monthly Income (Rs.)",
            bg=COLORS["card"],
            fg=COLORS["text"],
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        e_income = ttk.Entry(controls)
        e_income.pack(fill="x")
        e_income.focus_set()

        btn_row = tk.Frame(controls, bg=COLORS["card"])
        btn_row.pack(fill="x", pady=(10, 0))

        status_var = tk.StringVar(value="Enter income and click 'Generate Advice' (or press Enter).")
        tk.Label(btn_row, textvariable=status_var, bg=COLORS["card"], fg=COLORS["muted"], font=("Segoe UI", 9)).pack(side="left", padx=(0, 10))

        prog = ttk.Progressbar(btn_row, mode="indeterminate", length=160)

        out = tk.Text(inner, wrap="word", font=("Segoe UI", 10))
        out.pack(fill="both", expand=True)
        out.insert("1.0", "Enter income and click 'Generate Advice' (or press Enter).")

        busy = {"flag": False}

        def set_busy(is_busy: bool):
            busy["flag"] = is_busy
            if is_busy:
                status_var.set("Generating advice…")
                prog.pack(side="right")
                prog.start(10)
            else:
                prog.stop()
                prog.pack_forget()
                status_var.set("Done. You can try another income.")

        def ui_set_text(text: str):
            out.delete("1.0", "end")
            out.insert("1.0", text)

        def worker(income: float):
            try:
                rows = get_transactions(self.app.current_user)
                txt = recommend(rows, UserProfile(income=income))
            except Exception as e:
                txt = f"❌ Error while generating advice:\n{e}"

            out.after(0, lambda: ui_set_text(txt))
            out.after(0, lambda: set_busy(False))

        def run():
            if busy["flag"]:
                return

            raw = e_income.get().strip().replace(",", "")
            try:
                income = float(raw)
                if income <= 0:
                    raise ValueError("Income must be > 0")
            except Exception:
                ui_set_text("Please enter a valid number for income (e.g., 20000).")
                return

            set_busy(True)
            ui_set_text("Generating advice… please wait.")
            threading.Thread(target=worker, args=(income,), daemon=True).start()

        RoundedButton(
            btn_row,
            "Generate Advice",
            command=run,
            w=200,
            h=44,
            bg=COLORS["accent"],
            fg="white",
            hover_bg=COLORS["accent_hover"],
        ).pack(anchor="w", pady=(8, 0))

        e_income.bind("<Return>", lambda e: run())


# If you run ui.py directly
if __name__ == "__main__":
    App().mainloop()
