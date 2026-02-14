from __future__ import annotations
from typing import List, Tuple, Dict, Any
from datetime import datetime
import importlib

TxnRow = Tuple[int, float, str, str, str]  # (id, amount, category, note, tdate)

def _get_insights_module():
    # insights.py must be in same folder as main.py
    return importlib.import_module("insights")


def adapt_for_insights(rows: List[TxnRow], user_id: int = 1) -> List[Dict[str, Any]]:
    """
    Convert our GUI DB rows -> format that your insights.py analyze() expects.

    insights.py expects:
      amount_minor (int), txn_type, dt (datetime), date, description, category
    """
    out: List[Dict[str, Any]] = []

    for rid, amount, category, note, tdate in rows:
        # Parse date string from DB
        # Your insights.py parses first 10 chars as YYYY-MM-DD
        date_part = str(tdate)[:10]
        try:
            dt = datetime.strptime(date_part, "%Y-%m-%d")
        except Exception:
            # If date is missing/bad, skip this transaction
            continue

        amt = float(amount)

        # We currently only store expenses in GUI.
        # If you later add income, we’ll change this properly.
        txn_type = "expense"

        out.append({
            "id": rid,
            "user_id": user_id,

            # insights uses minor units: 100 minor = 1 major currency
            "amount_minor": int(round(amt * 100)),

            "txn_type": txn_type,
            "dt": dt,
            "date": dt.date(),
            "description": (note or "").strip(),
            "category": (category or "Uncategorized").strip(),
        })

    return out


def run_insights(rows: List[TxnRow]) -> str:
    try:
        insights = _get_insights_module()
    except Exception as e:
        return f"Could not import insights.py: {e}"

    payload = adapt_for_insights(rows, user_id=1)

    try:
        return insights.analyze(payload)
    except Exception as e:
        return f"insights.analyze() crashed: {e}"
