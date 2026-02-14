"""
Spending Insights / Pattern Analyzer for your finance.db

What it does (for user_id=1 by default):
- Monthly summary: income, expenses, net savings
- Month-over-month deltas: "spent X more/less than previous month"
- Category changes: "spent more on Healthcare this month"
- Weekly patterns: weekly totals + top categories by week
- Day-of-week patterns: where you spend the most (Mon..Sun)
- “Creative” insights: biggest single expense, most frequent merchant/description,
  “habit” detection (recurring bills), and simple anomaly detection.
"""

import sqlite3
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any

DB_PATH = Path("db/finance.db")


def fetch_transactions(conn: sqlite3.Connection, user_id: int) -> List[Dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
          t.id,
          t.user_id,
          t.amount_minor,
          t.txn_type,
          t.txn_date,
          t.description,
          t.category_id,
          COALESCE(c.name, 'Uncategorized') AS category_name
        FROM transactions t
        LEFT JOIN categories c ON c.id = t.category_id
        WHERE t.user_id = ?
        ORDER BY t.txn_date ASC
        """,
        (user_id,),
    )
    rows = cur.fetchall()
    out = []
    for r in rows:
        # txn_date is stored as text; assume YYYY-MM-DD or ISO.
        # We'll parse the first 10 chars safely as date.
        date_part = str(r["txn_date"])[:10]
        dt = datetime.strptime(date_part, "%Y-%m-%d")
        out.append(
            {
                "id": r["id"],
                "user_id": r["user_id"],
                "amount_minor": int(r["amount_minor"]),
                "txn_type": r["txn_type"],
                "dt": dt,
                "date": dt.date(),
                "description": (r["description"] or "").strip(),
                "category": (r["category_name"] or "Uncategorized").strip(),
            }
        )
    return out


def minor_to_major(amount_minor: int) -> float:
    # You’re storing “minor units”. Commonly: 100 minor = 1 major.
    # If you use PKR without decimals, you can change /100 to /1.
    return amount_minor / 100.0


def ym_key(dt: datetime) -> str:
    return dt.strftime("%Y-%m")


def week_key(dt: datetime) -> str:
    # ISO week is great for weekly patterns
    iso_year, iso_week, _ = dt.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def analyze(transactions: List[Dict[str, Any]]) -> str:
    if not transactions:
        return "No transactions found."

    # Split income vs expense
    income = [t for t in transactions if t["txn_type"] == "income"]
    expense = [t for t in transactions if t["txn_type"] == "expense"]

    # --- Monthly totals ---
    monthly_income = defaultdict(int)
    monthly_expense = defaultdict(int)
    monthly_category_expense = defaultdict(lambda: defaultdict(int))  # month -> cat -> amt

    for t in income:
        monthly_income[ym_key(t["dt"])] += t["amount_minor"]

    for t in expense:
        m = ym_key(t["dt"])
        monthly_expense[m] += t["amount_minor"]
        monthly_category_expense[m][t["category"]] += t["amount_minor"]

    months = sorted(set(list(monthly_income.keys()) + list(monthly_expense.keys())))

    # --- Weekly totals + weekly category ---
    weekly_expense = defaultdict(int)
    weekly_category_expense = defaultdict(lambda: defaultdict(int))
    for t in expense:
        w = week_key(t["dt"])
        weekly_expense[w] += t["amount_minor"]
        weekly_category_expense[w][t["category"]] += t["amount_minor"]

    weeks = sorted(weekly_expense.keys())

    # --- Day-of-week patterns ---
    # Monday=0 ... Sunday=6
    dow_expense = defaultdict(int)
    dow_counts = defaultdict(int)
    for t in expense:
        d = t["dt"].weekday()
        dow_expense[d] += t["amount_minor"]
        dow_counts[d] += 1

    # --- Descriptions / habits ---
    desc_counts = Counter([t["description"].lower() for t in expense if t["description"]])
    biggest_exp = max(expense, key=lambda x: x["amount_minor"]) if expense else None

    # Simple recurring detection: same description appears >=2 times
    recurring = [(d, c) for d, c in desc_counts.items() if c >= 2]
    recurring.sort(key=lambda x: (-x[1], x[0]))

    # Simple anomaly: expenses > (mean + 2*std) within each month
    # (No numpy; do manually)
    anomalies = []
    by_month_expenses = defaultdict(list)
    for t in expense:
        by_month_expenses[ym_key(t["dt"])].append(t["amount_minor"])

    for m, vals in by_month_expenses.items():
        if len(vals) < 5:
            continue
        mean = sum(vals) / len(vals)
        var = sum((v - mean) ** 2 for v in vals) / len(vals)
        std = var ** 0.5
        threshold = mean + 2 * std
        for t in expense:
            if ym_key(t["dt"]) == m and t["amount_minor"] > threshold:
                anomalies.append((m, t))

    # --- Build insights text ---
    lines = []
    lines.append("📊 SPENDING INSIGHTS\n")

    # Monthly summary
    lines.append("🗓️ Monthly Summary:")
    for m in months:
        inc = monthly_income.get(m, 0)
        exp = monthly_expense.get(m, 0)
        net = inc - exp
        lines.append(
            f"  - {m}: Income {minor_to_major(inc):,.2f}, "
            f"Expenses {minor_to_major(exp):,.2f}, "
            f"Net {minor_to_major(net):,.2f}"
        )

    # Month-over-month expense change
    if len(months) >= 2:
        lines.append("\n📈 Month-over-Month Changes (Expenses):")
        for i in range(1, len(months)):
            prev_m = months[i - 1]
            cur_m = months[i]
            prev_exp = monthly_expense.get(prev_m, 0)
            cur_exp = monthly_expense.get(cur_m, 0)
            diff = cur_exp - prev_exp
            if diff > 0:
                lines.append(
                    f"  - In {cur_m}, you spent {minor_to_major(diff):,.2f} more than {prev_m}."
                )
            elif diff < 0:
                lines.append(
                    f"  - In {cur_m}, you spent {minor_to_major(-diff):,.2f} less than {prev_m}."
                )
            else:
                lines.append(f"  - In {cur_m}, your spending was the same as {prev_m}.")

    # Category shifts month over month
    if len(months) >= 2:
        lines.append("\n🏷️ Category Changes (this month vs previous):")
        for i in range(1, len(months)):
            prev_m = months[i - 1]
            cur_m = months[i]
            prev_cats = monthly_category_expense.get(prev_m, {})
            cur_cats = monthly_category_expense.get(cur_m, {})
            all_cats = sorted(set(prev_cats.keys()) | set(cur_cats.keys()))
            changes = []
            for cat in all_cats:
                d = cur_cats.get(cat, 0) - prev_cats.get(cat, 0)
                if d != 0:
                    changes.append((abs(d), d, cat))
            changes.sort(reverse=True)  # biggest change first
            if not changes:
                lines.append(f"  - {cur_m}: No category changes from {prev_m}.")
            else:
                top = changes[:3]
                lines.append(f"  - {cur_m} vs {prev_m}:")
                for _, d, cat in top:
                    if d > 0:
                        lines.append(
                            f"      • {cat}: +{minor_to_major(d):,.2f} (spent more)"
                        )
                    else:
                        lines.append(
                            f"      • {cat}: -{minor_to_major(-d):,.2f} (spent less)"
                        )

    # Weekly patterns
    if weeks:
        lines.append("\n📅 Weekly Spending (Expenses):")
        for w in weeks:
            total = weekly_expense[w]
            # top category in the week
            cats = weekly_category_expense[w]
            top_cat, top_amt = max(cats.items(), key=lambda x: x[1])
            lines.append(
                f"  - {w}: {minor_to_major(total):,.2f} (top: {top_cat} {minor_to_major(top_amt):,.2f})"
            )

        # Trend: compare last week vs previous
        if len(weeks) >= 2:
            prev_w, cur_w = weeks[-2], weeks[-1]
            diff = weekly_expense[cur_w] - weekly_expense[prev_w]
            lines.append("\n📌 Weekly Trend:")
            if diff > 0:
                lines.append(
                    f"  - Last week ({cur_w}) you spent {minor_to_major(diff):,.2f} more than ({prev_w})."
                )
            elif diff < 0:
                lines.append(
                    f"  - Last week ({cur_w}) you spent {minor_to_major(-diff):,.2f} less than ({prev_w})."
                )
            else:
                lines.append(f"  - Last week ({cur_w}) spending matched ({prev_w}).")

    # Day-of-week insight
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    if dow_expense:
        best_day = max(dow_expense.items(), key=lambda x: x[1])[0]
        lines.append("\n🧭 Day-of-Week Pattern:")
        lines.append(
            f"  - Highest spending day: {day_names[best_day]} "
            f"({minor_to_major(dow_expense[best_day]):,.2f} across {dow_counts[best_day]} transactions)"
        )
        # show distribution
        lines.append("  - Breakdown:")
        for d in range(7):
            if dow_counts[d] == 0:
                continue
            avg = dow_expense[d] / dow_counts[d]
            lines.append(
                f"      • {day_names[d]}: total {minor_to_major(dow_expense[d]):,.2f}, "
                f"avg {minor_to_major(int(avg)):,.2f} per txn, n={dow_counts[d]}"
            )

    # Big ticket + frequency
    lines.append("\n💥 Big / Habit Insights:")
    if biggest_exp:
        lines.append(
            f"  - Biggest single expense: {biggest_exp['description'] or 'Expense'} on "
            f"{biggest_exp['date']} = {minor_to_major(biggest_exp['amount_minor']):,.2f} "
            f"(category: {biggest_exp['category']})"
        )

    if recurring:
        lines.append("  - Recurring / repeated purchases (by description):")
        for desc, cnt in recurring[:5]:
            lines.append(f"      • '{desc}' repeated {cnt} times")

    # Anomalies
    if anomalies:
        lines.append("\n🚨 Unusual Transactions (possible anomalies):")
        for m, t in anomalies[:5]:
            lines.append(
                f"  - {m}: {t['description'] or 'Expense'} on {t['date']} = "
                f"{minor_to_major(t['amount_minor']):,.2f} (category: {t['category']})"
            )

    # Budget-ish suggestion (simple)
    if len(months) >= 1:
        latest = months[-1]
        exp = monthly_expense.get(latest, 0)
        inc = monthly_income.get(latest, 0)
        if inc > 0:
            ratio = exp / inc
            lines.append("\n🎯 Simple Score:")
            lines.append(
                f"  - In {latest}, you spent {ratio*100:.1f}% of your income."
            )
            if ratio > 0.9:
                lines.append("  - ⚠️ You’re spending close to your income. Consider cutting the top category.")
            elif ratio > 0.7:
                lines.append("  - 👍 Decent. You still have room to save more by trimming non-essentials.")
            else:
                lines.append("  - ✅ Strong saving month. Keep it consistent.")

    return "\n".join(lines)


def main(user_id: int = 1):
    if not DB_PATH.exists():
        print(f"DB not found at {DB_PATH.resolve()}. Run init_db.py first.")
        return

    conn = sqlite3.connect(DB_PATH)
    txns = fetch_transactions(conn, user_id=user_id)
    conn.close()

    report = analyze(txns)
    print(report)


if __name__ == "__main__":
    main(user_id=1)
