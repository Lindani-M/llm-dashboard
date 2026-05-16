import pandas as pd
import os
from pathlib import Path


def get_excel_path() -> Path:
    env_path = os.getenv("EXCEL_PATH")
    if env_path:
        return Path(env_path)
    return Path(__file__).parent.parent / "Bank_Churn.xlsx"


def compute_metrics() -> dict:
    df = pd.read_excel(get_excel_path())

    total = len(df)
    churned = int(df["Exited"].sum())
    retained = total - churned

    kpis = {
        "total_customers": total,
        "churned_customers": churned,
        "retained_customers": retained,
        "churn_rate": round(churned / total * 100, 1),
        "retention_rate": round(retained / total * 100, 1),
        "avg_balance_churned": round(float(df[df["Exited"] == 1]["Balance"].mean()), 0),
        "avg_balance_retained": round(float(df[df["Exited"] == 0]["Balance"].mean()), 0),
    }

    # Geography
    geography = {}
    for geo in ["France", "Spain", "Germany"]:
        g = df[df["Geography"] == geo]
        gc = int(g["Exited"].sum())
        gt = len(g)
        geography[geo] = {
            "total": gt,
            "churned": gc,
            "retained": gt - gc,
            "churn_rate": round(gc / gt * 100, 1),
        }

    # Age groups
    bins = [0, 29, 39, 49, 59, 200]
    labels = ["18-29", "30-39", "40-49", "50-59", "60+"]
    df["age_group"] = pd.cut(df["Age"], bins=bins, labels=labels)
    age = {}
    for label in labels:
        g = df[df["age_group"] == label]
        if len(g) > 0:
            gc = int(g["Exited"].sum())
            age[label] = {
                "total": len(g),
                "churned": gc,
                "retained": len(g) - gc,
                "churn_rate": round(gc / len(g) * 100, 1),
            }

    # Gender
    gender = {}
    for g_val in ["Male", "Female"]:
        g = df[df["Gender"] == g_val]
        gc = int(g["Exited"].sum())
        gender[g_val] = {
            "total": len(g),
            "churned": gc,
            "retained": len(g) - gc,
            "churn_rate": round(gc / len(g) * 100, 1),
        }

    # NumOfProducts
    products = {}
    for n in [1, 2, 3, 4]:
        g = df[df["NumOfProducts"] == n]
        if len(g) > 0:
            gc = int(g["Exited"].sum())
            products[str(n)] = {
                "total": len(g),
                "churned": gc,
                "churn_rate": round(gc / len(g) * 100, 1),
            }

    # Activity
    activity = {}
    for name, val in [("Active", 1), ("Inactive", 0)]:
        g = df[df["IsActiveMember"] == val]
        gc = int(g["Exited"].sum())
        activity[name] = {
            "total": len(g),
            "churned": gc,
            "retained": len(g) - gc,
            "churn_rate": round(gc / len(g) * 100, 1),
        }

    # Balance
    zero_bal = df[df["Balance"] <= 0]
    has_bal = df[df["Balance"] > 0]
    balance = {
        "Zero Balance": {
            "total": len(zero_bal),
            "churned": int(zero_bal["Exited"].sum()),
            "churn_rate": round(float(zero_bal["Exited"].mean()) * 100, 1),
        },
        "Has Balance": {
            "total": len(has_bal),
            "churned": int(has_bal["Exited"].sum()),
            "churn_rate": round(float(has_bal["Exited"].mean()) * 100, 1),
        },
    }

    # Credit score bands
    cs_bins = [0, 499, 599, 699, 799, 1000]
    cs_labels = ["<500", "500-599", "600-699", "700-799", "800+"]
    df["cs_group"] = pd.cut(df["CreditScore"], bins=cs_bins, labels=cs_labels)
    credit_score = {}
    for label in cs_labels:
        g = df[df["cs_group"] == label]
        if len(g) > 0:
            credit_score[label] = {
                "total": len(g),
                "churned": int(g["Exited"].sum()),
                "churn_rate": round(float(g["Exited"].mean()) * 100, 1),
            }

    # Tenure (0-10 years)
    tenure = {}
    for t in range(0, 11):
        g = df[df["Tenure"] == t]
        if len(g) > 0:
            gc = int(g["Exited"].sum())
            tenure[str(t)] = {
                "total": len(g),
                "churned": gc,
                "churn_rate": round(gc / len(g) * 100, 1),
            }

    return {
        "kpis": kpis,
        "geography": geography,
        "age": age,
        "gender": gender,
        "products": products,
        "activity": activity,
        "balance": balance,
        "credit_score": credit_score,
        "tenure": tenure,
    }
