from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from pathlib import Path

TxnRow = Tuple[int, float, str, str, str]  # (id, amount, category, note, tdate)

CATEGORY_MAP = {
    "rent": "Rent",
    "loan": "Loan_Repayment",
    "repayment": "Loan_Repayment",
    "insurance": "Insurance",
    "grocery": "Groceries",
    "groceries": "Groceries",
    "food": "Groceries",
    "transport": "Transport",
    "ride": "Transport",
    "fuel": "Transport",
    "eating out": "Eating_Out",
    "restaurant": "Eating_Out",
    "fast food": "Eating_Out",
    "entertainment": "Entertainment",
    "utilities": "Utilities",
    "bill": "Utilities",
    "health": "Healthcare",
    "healthcare": "Healthcare",
    "education": "Education",
    "study": "Education",
    "misc": "Miscellaneous",
    "miscellaneous": "Miscellaneous",
    "other": "Miscellaneous",
}

SPEND_COLS = [
    "Rent", "Loan_Repayment", "Insurance", "Groceries", "Transport", "Eating_Out",
    "Entertainment", "Utilities", "Healthcare", "Education", "Miscellaneous"
]

def _normalize_cat(cat: str) -> str:
    c = (cat or "").strip().lower()
    return CATEGORY_MAP.get(c, "Miscellaneous")

def app_rows_to_budget_inputs(rows: List[TxnRow]) -> Dict[str, float]:
    spend = {k: 0.0 for k in SPEND_COLS}
    for _id, amount, category, note, tdate in rows:
        col = _normalize_cat(category)
        spend[col] += float(amount)
    return spend

@dataclass
class UserProfile:
    income: float
    age: int = 30
    dependents: int = 0
    occupation: str = "Unknown"
    city_tier: str = "Tier_2"

# ---------------------------
# AI Savings Coach
# ---------------------------

def recommend(rows: List[TxnRow], profile: UserProfile) -> str:
    """AI Savings Coach - Heuristic-based recommendations."""
    
    spend = app_rows_to_budget_inputs(rows)
    total_spent = sum(spend.values())
    
    income = float(profile.income)
    
    # Heuristic: recommended savings = 20% of income
    recommended_savings_pct = 20.0
    recommended_savings = income * (recommended_savings_pct / 100.0)
    disposable = income - total_spent if total_spent > 0 else income
    
    # Identify top spending categories
    top_spending = sorted([(cat, amt) for cat, amt in spend.items() if amt > 0], 
                         key=lambda x: x[1], reverse=True)[:3]
    
    # Heuristic savings potential: 15-25% reduction in top categories
    potentials = {}
    for cat, amt in spend.items():
        if amt > 0:
            potentials[cat] = amt * 0.20  # 20% potential savings per category
        else:
            potentials[cat] = 0.0
    
    top_potential = sorted([(cat, amt) for cat, amt in potentials.items() if amt > 0], 
                          key=lambda x: x[1], reverse=True)[:3]
    total_potential = sum(v for v in potentials.values())
    
    lines = []
    lines.append("💡 AI SAVINGS COACH (Smart Analysis)\n")
    lines.append(f"📊 Income: Rs. {income:,.0f}")
    lines.append(f"💰 Total Spending: Rs. {total_spent:,.0f}")
    lines.append(f"🎯 Disposable Income: Rs. {disposable:,.0f}")
    lines.append(f"✅ Recommended Savings: {recommended_savings_pct}% = Rs. {recommended_savings:,.0f}\n")
    
    lines.append("📈 Your Spending Breakdown:")
    for cat, amt in sorted([(c, a) for c, a in spend.items() if a > 0], key=lambda x: x[1], reverse=True):
        pct = (amt / income * 100) if income > 0 else 0
        lines.append(f"  • {cat}: Rs. {amt:,.0f} ({pct:.1f}% of income)")
    
    if not any(v > 0 for v in spend.values()):
        lines.append("  (No transactions yet)")
    lines.append("")
    
    lines.append("🔍 Smart Saving Opportunities:")
    if top_potential:
        for cat, potential in top_potential:
            current = spend.get(cat, 0)
            lines.append(f"  ✅ {cat}: Save ~Rs. {potential:,.0f}/month")
            lines.append(f"      (Currently: Rs. {current:,.0f} → Target: Rs. {current - potential:,.0f})")
    else:
        lines.append("  ✅ Great job! Your spending is well-balanced.")
    
    lines.append(f"\n💡 Total Potential Savings: ~Rs. {total_potential:,.0f}/month\n")
    
    lines.append("📋 Action Plan:")
    if top_potential:
        lines.append(f"1️⃣  Start with {top_potential[0][0]} - save ~Rs. {top_potential[0][1]:,.0f}")
        if len(top_potential) > 1:
            lines.append(f"2️⃣  Then target {top_potential[1][0]} - save ~Rs. {top_potential[1][1]:,.0f}")
        else:
            lines.append(f"2️⃣  Set weekly spending caps for {top_potential[0][0]}")
        lines.append("3️⃣  Review your spending weekly")
        lines.append("4️⃣  Automate savings first - rest comes second")
    else:
        lines.append("1️⃣  Set a savings goal of 20% of your income")
        lines.append("2️⃣  Track spending in detail")
        lines.append("3️⃣  Automate transfers to savings account")
    
    lines.append("\n🎓 Money Wisdom: 'Don't save what's left after spending. Spend what's left after saving.' - Warren Buffett")
    
    return "\n".join(lines)
