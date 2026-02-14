from __future__ import annotations
from pathlib import Path
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor

MODEL_PATH = Path("model_budget.joblib")

SPEND_COLS = [
    "Rent","Loan_Repayment","Insurance","Groceries","Transport","Eating_Out",
    "Entertainment","Utilities","Healthcare","Education","Miscellaneous"
]

TARGET_COLS = [
    "Desired_Savings_Percentage",
    "Desired_Savings",
    "Disposable_Income",
    "Potential_Savings_Groceries",
    "Potential_Savings_Transport",
    "Potential_Savings_Eating_Out",
    "Potential_Savings_Entertainment",
    "Potential_Savings_Utilities",
    "Potential_Savings_Healthcare",
    "Potential_Savings_Education",
    "Potential_Savings_Miscellaneous",
]

BASE_FEATURES = ["Income", "Age", "Dependents", "Occupation", "City_Tier"] + SPEND_COLS


def load_and_clean(csv_path: str | Path) -> pd.DataFrame:
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path.resolve()}")

    df = pd.read_csv(csv_path)

    missing = [c for c in BASE_FEATURES + TARGET_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"CSV missing columns: {missing}")

    # numeric cleanup
    for c in ["Income","Age","Dependents"] + SPEND_COLS + TARGET_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df["Occupation"] = df["Occupation"].astype(str).fillna("Unknown")
    df["City_Tier"] = df["City_Tier"].astype(str).fillna("Unknown")

    df = df.dropna(subset=["Income"] + SPEND_COLS)  # must have income and spend cols
    return df


def main(csv_path="data.csv"):
    df = load_and_clean(csv_path)

    X = df[BASE_FEATURES]
    y = df[TARGET_COLS]

    categorical = ["Occupation", "City_Tier"]
    numeric = [c for c in BASE_FEATURES if c not in categorical]

    pre = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
            ("num", "passthrough", numeric),
        ]
    )

    # Solid starter model; easy, stable
    base = RandomForestRegressor(
        n_estimators=300,
        random_state=42,
        n_jobs=-1,
        max_depth=None
    )

    model = Pipeline([
        ("pre", pre),
        ("reg", MultiOutputRegressor(base))
    ])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
    model.fit(X_train, y_train)

    payload = {
        "model": model,
        "features": BASE_FEATURES,
        "targets": TARGET_COLS,
        "spend_cols": SPEND_COLS,
        "train_medians": {
            "Income": float(df["Income"].median()),
            "Age": float(df["Age"].median()),
            "Dependents": float(df["Dependents"].median()),
            "Occupation": df["Occupation"].mode().iloc[0],
            "City_Tier": df["City_Tier"].mode().iloc[0],
        }
    }

    joblib.dump(payload, MODEL_PATH)
    print(f"✅ Saved model to: {MODEL_PATH.resolve()}")


if __name__ == "__main__":
    import sys
    csv = sys.argv[1] if len(sys.argv) > 1 else "data.csv"
    main(csv)

