from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import threading
import joblib
import pandas as pd  # moved to top so import doesn't stall on first click

# IMPORTANT: model loads relative to THIS file, not your run folder
MODEL_PATH = Path(__file__).resolve().parent / "model_budget.joblib"

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
# ✅ Cached model loading (NO FREEZE)
# ---------------------------
_model_lock = threading.Lock()
_cached_pkg: Optional[dict] = None
_cached_error: Optional[str] = None

def _get_model_package() -> Optional[dict]:
    """
    Load the model package ONCE and cache it.
    Thread-safe so it won't load multiple times if user clicks fast.
    """
    global _cached_pkg, _cached_error

    # already loaded
    if _cached_pkg is not None:
        return _cached_pkg

    # already failed before
    if _cached_error is not None:
        return None

    with _model_lock:
        if _cached_pkg is not None:
            return _cached_pkg
        if _cached_error is not None:
            return None

        if not MODEL_PATH.exists():
            _cached_error = (
                "Model not found.\n"
                f"Expected: {MODEL_PATH.resolve()}\n"
                "Train it first to create model_budget.joblib"
            )
            return None

        try:
            _cached_pkg = joblib.load(MODEL_PATH)
            return _cached_pkg
        except Exception as e:
            _cached_error = f"Failed to load model at {MODEL_PATH.resolve()}\nError: {e}"
            return None

def get_model_status_message() -> Optional[str]:
    """
    If model failed to load, return the error message (else None).
    Helpful for UI to display a clean message.
    """
    global _cached_error
    if _cached_error is not None:
        return _cached_error
    return None

def recommend(rows: List[TxnRow], profile: UserProfile) -> str:
    pkg = _get_model_package()
    if pkg is None:
        msg = get_model_status_message()
        return msg or "Model unavailable due to unknown error."

    # Validate required keys early
    for key in ("model", "features", "targets"):
        if key not in pkg:
            return f"Model package is missing '{key}'. Re-train and save correct keys."

    model = pkg["model"]
    feats = pkg["features"]
    tcols = pkg["targets"]

    spend = app_rows_to_budget_inputs(rows)

    x = {
        "Income": float(profile.income),
        "Age": int(profile.age),
        "Dependents": int(profile.dependents),
        "Occupation": str(profile.occupation),
        "City_Tier": str(profile.city_tier),
        **spend,
    }

    # Build dataframe in the same column order the model expects
    X = pd.DataFrame([x], columns=feats)

    pred = model.predict(X)[0]
    pred_dict = dict(zip(tcols, pred))

    desired_pct = float(pred_dict.get("Desired_Savings_Percentage", 0.0))
    desired_sav = float(pred_dict.get("Desired_Savings", 0.0))
    disposable = float(pred_dict.get("Disposable_Income", 0.0))

    potentials = {
        "Groceries": float(pred_dict.get("Potential_Savings_Groceries", 0.0)),
        "Transport": float(pred_dict.get("Potential_Savings_Transport", 0.0)),
        "Eating_Out": float(pred_dict.get("Potential_Savings_Eating_Out", 0.0)),
        "Entertainment": float(pred_dict.get("Potential_Savings_Entertainment", 0.0)),
        "Utilities": float(pred_dict.get("Potential_Savings_Utilities", 0.0)),
        "Healthcare": float(pred_dict.get("Potential_Savings_Healthcare", 0.0)),
        "Education": float(pred_dict.get("Potential_Savings_Education", 0.0)),
        "Miscellaneous": float(pred_dict.get("Potential_Savings_Miscellaneous", 0.0)),
    }

    top = sorted(potentials.items(), key=lambda x: x[1], reverse=True)[:3]
    total_possible = sum(max(v, 0.0) for v in potentials.values())

    lines = []
    lines.append("💡 SAVINGS COACH (Trained on CSV patterns)\n")
    lines.append(f"Income used: Rs. {profile.income:,.0f}")
    lines.append(f"Estimated disposable income: Rs. {disposable:,.0f}")
    lines.append(f"Suggested savings rate: {desired_pct:.1f}%")
    lines.append(f"Suggested savings amount: Rs. {desired_sav:,.0f}\n")

    lines.append("Your app spending totals:")
    for k, v in sorted(spend.items(), key=lambda x: x[1], reverse=True):
        if v > 0:
            lines.append(f"• {k}: Rs. {v:,.0f}")
    lines.append("")

    lines.append("Top saving opportunities (model):")
    shown_any = False
    for cat, val in top:
        if val > 0:
            shown_any = True
            lines.append(f"✅ {cat}: save ~Rs. {val:,.0f}")
    if not shown_any:
        lines.append("✅ No strong savings opportunities detected from the model.")
    lines.append(f"\nTotal potential savings: ~Rs. {total_possible:,.0f}\n")

    lines.append("Action plan:")
    if top and top[0][1] > 0:
        lines.append(f"1) Reduce {top[0][0]} by ~Rs. {top[0][1]:,.0f}")
    else:
        lines.append("1) Set a simple saving target (start with 10% if unsure).")
    lines.append("2) Set weekly caps for top 2 categories.")
    lines.append("3) Review History weekly and save first.")

    return "\n".join(lines)
