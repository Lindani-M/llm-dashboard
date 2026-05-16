import io
import base64
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
import msal

logger = logging.getLogger("dashboard.metrics")

# ── SharePoint / Graph API helpers ──────────────────────────────────────────

_SP_TENANT_ID = os.getenv("SP_TENANT_ID", "")
_SP_CLIENT_ID = os.getenv("SP_CLIENT_ID", "")
_SP_CLIENT_SECRET = os.getenv("SP_CLIENT_SECRET", "")
# Full sharing URL to the Excel file on SharePoint
_SP_FILE_SHARE_URL = os.getenv(
    "SP_FILE_SHARE_URL",
    "https://roleio.sharepoint.com/:x:/s/MScDocuments/IQD1HkpJfyj4RrzlS-uxtQ1WAbf9OSppcUOrqsCvTUHI_f0?e=ZcEHVi",
)
_GRAPH_SCOPE = ["https://graph.microsoft.com/.default"]


def _get_graph_token() -> str:
    """Acquire an app-only token for Microsoft Graph using client credentials."""
    authority = f"https://login.microsoftonline.com/{_SP_TENANT_ID}"
    app = msal.ConfidentialClientApplication(
        _SP_CLIENT_ID,
        authority=authority,
        client_credential=_SP_CLIENT_SECRET,
        azure_region=False,  # disable region auto-detection (suppress warning)
    )
    result = app.acquire_token_for_client(scopes=_GRAPH_SCOPE)
    if "access_token" not in result:
        raise RuntimeError(f"MSAL token error: {result.get('error_description', result)}")
    return result["access_token"]


def _share_url_to_encoded_id(url: str) -> str:
    """Convert a SharePoint sharing URL to the Graph API encoded share ID."""
    b64 = base64.b64encode(url.encode()).decode().rstrip("=")
    b64 = b64.replace("/", "_").replace("+", "-")
    return "u!" + b64


def _get_sharepoint_drive_item() -> dict:
    """Return the Graph driveItem metadata for the SharePoint file."""
    token = _get_graph_token()
    share_id = _share_url_to_encoded_id(_SP_FILE_SHARE_URL)
    url = f"https://graph.microsoft.com/v1.0/shares/{share_id}/driveItem"
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_excel_mtime() -> datetime:
    """Return the SharePoint file's lastModifiedDateTime as a UTC-aware datetime.
    Falls back to local file mtime when SharePoint env vars are not configured."""
    if not _SP_TENANT_ID or not _SP_CLIENT_ID or not _SP_CLIENT_SECRET:
        logger.warning("SharePoint credentials not set — falling back to local file mtime")
        local = _get_local_excel_path()
        return datetime.fromtimestamp(local.stat().st_mtime, tz=timezone.utc)
    try:
        item = _get_sharepoint_drive_item()
        raw = item["lastModifiedDateTime"]  # e.g. "2026-05-16T13:34:44Z"
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        logger.info("SharePoint file last modified: %s", dt.isoformat())
        return dt
    except Exception as e:
        logger.error("Failed to get SharePoint mtime, falling back: %s", e)
        local = _get_local_excel_path()
        return datetime.fromtimestamp(local.stat().st_mtime, tz=timezone.utc)


def _download_excel() -> Path:
    """Download the Excel file from SharePoint to a temp file and return its path."""
    if not _SP_TENANT_ID or not _SP_CLIENT_ID or not _SP_CLIENT_SECRET:
        logger.info("SharePoint not configured — using local Excel file")
        return _get_local_excel_path()
    logger.info("Downloading Excel from SharePoint…")
    token = _get_graph_token()
    share_id = _share_url_to_encoded_id(_SP_FILE_SHARE_URL)
    url = f"https://graph.microsoft.com/v1.0/shares/{share_id}/driveItem/content"
    resp = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=60,
        allow_redirects=True,
    )
    resp.raise_for_status()
    # Write to a stable temp path so pandas can read it
    tmp = Path(tempfile.gettempdir()) / "Bank_Churn_sp.xlsx"
    tmp.write_bytes(resp.content)
    logger.info("SharePoint file downloaded (%d bytes) → %s", len(resp.content), tmp)
    return tmp


def _get_local_excel_path() -> Path:
    env_path = os.getenv("EXCEL_PATH")
    if env_path:
        return Path(env_path)
    return Path(__file__).parent.parent / "Bank_Churn.xlsx"


def compute_metrics() -> dict:
    df = pd.read_excel(_download_excel())

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
