from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple

TxnRow = Tuple[int, float, str, str, str]  # (id, amount, category, note, tdate)


def totals_by_category(rows: List[TxnRow]) -> Dict[str, float]:
    d = defaultdict(float)
    for _, amount, category, _, _ in rows:
        d[category or "Other"] += float(amount)
    return dict(d)


def totals_by_month(rows: List[TxnRow]) -> Dict[str, float]:
    d = defaultdict(float)
    for _, amount, _, _, tdate in rows:
        key = (tdate or "")[:7]  # "YYYY-MM"
        if len(key) == 7:
            d[key] += float(amount)
    return dict(sorted(d.items()))


def totals_by_week(rows: List[TxnRow]) -> Dict[str, float]:
    d = defaultdict(float)
    for _, amount, _, _, tdate in rows:
        try:
            dt = datetime.strptime(tdate, "%Y-%m-%d")
            iso = dt.isocalendar()  # (year, week, weekday)
            key = f"{iso.year}-W{iso.week:02d}"
            d[key] += float(amount)
        except Exception:
            continue
    return dict(sorted(d.items()))
