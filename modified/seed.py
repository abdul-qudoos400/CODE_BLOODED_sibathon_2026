from db import ensure_user, add_transaction, count_transactions

DEMO_USER = "sarakatpar"
DEMO_PASS = "sarakatpar1"

SAMPLE_TXNS = [
    # (amount, category, note, date)
    (1200, "Food", "burger", "2026-01-03"),
    (500, "Transport", "rickshaw", "2026-01-04"),
    (3000, "Shopping", "clothes", "2026-01-10"),
    (1500, "Bills", "internet", "2026-01-15"),
    (900, "Food", "pizza", "2026-01-18"),
    (2000, "Health", "medicine", "2026-01-23"),
    (700, "Transport", "fuel", "2026-02-02"),
    (2300, "Food", "family dinner", "2026-02-07"),
    (1100, "Bills", "electricity", "2026-02-11"),
    (4500, "Shopping", "shoes", "2026-02-15"),
    (800, "Food", "snacks", "2026-02-20"),
    (1200, "Entertainment", "cinema", "2026-02-22"),
    (950, "Transport", "ride", "2026-03-01"),
    (1700, "Food", "groceries", "2026-03-03"),
    (2600, "Bills", "gas", "2026-03-05"),
    (5000, "Shopping", "gadgets", "2026-03-08"),
    (1300, "Health", "checkup", "2026-03-10"),
    (900, "Entertainment", "games", "2026-03-12"),
]

def seed_demo_if_needed():
    ensure_user(DEMO_USER, DEMO_PASS)

    # If no transactions, insert sample ones
    if count_transactions(DEMO_USER) == 0:
        for amt, cat, note, dt in SAMPLE_TXNS:
            add_transaction(DEMO_USER, amt, cat, note, dt)
