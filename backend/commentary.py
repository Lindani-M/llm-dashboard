import json
from datetime import datetime, timezone
from pathlib import Path
from metrics import compute_metrics
from ai_client import generate_commentary

STORE_PATH = Path(__file__).parent / "commentary_store.json"

SECTION_IDS = [
    "executive_summary",
    "section_subtitle",
    "geography_insight",
    "age_insight",
    "inactive_members_body",
    "multi_product_body",
    "female_customers_body",
    "germany_body",
    "products_insight",
    "credit_score_insight",
    "activity_balance_insight",
    "tenure_insight",
    "strategic_recommendations",
    # Editable labels (user-only, no AI regeneration)
    "grantee_title_inactive",
    "grantee_title_multiproduct",
    "grantee_title_female",
    "grantee_title_germany",
]

# Seeded from the original HTML dashboard — shown immediately on first launch
# before AI generation has run.
DEFAULT_COMMENTARY = {
    "executive_summary": (
        "The overall churn rate stands at <strong>20.4%</strong> (2,037 of 10,000 customers). "
        "Germany shows a disproportionately high churn rate of <strong>32.4%</strong>, nearly double "
        "that of France (16.2%) and Spain (16.7%). Female customers churn at <strong>25.1%</strong> "
        "vs. 16.5% for males, and customers with 3+ products churn at <strong>82.7–100%</strong> — "
        "suggesting a cross-sell strategy that may be backfiring. Churned customers carry "
        "<strong>25% higher balances</strong> on average ($91K vs $73K), representing significant revenue at risk."
    ),
    "geography_insight": (
        "<strong>Key insight:</strong> Germany accounts for 25% of total customers but "
        "<strong>40% of all churn</strong>. Regional service quality or competitive dynamics warrant urgent investigation."
    ),
    "age_insight": (
        "<strong>Critical finding:</strong> The 50–59 age band has a <strong>56% churn rate</strong> — "
        "the highest-risk segment. These are likely high-value clients approaching wealth transition. "
        "The 40–49 band (30.8%) is an early-warning zone."
    ),
    "inactive_members_body": (
        "Inactive members churn at nearly double the rate of active members. "
        "This segment represents the single largest addressable risk pool — re-engagement campaigns "
        "could prevent an estimated 600+ departures annually."
    ),
    "multi_product_body": (
        "Customers holding 3 or more products churn at 82.7–100%, a counter-intuitive finding that "
        "suggests complexity or fee fatigue. All 60 customers with 4 products exited. "
        "Cross-sell strategies must be re-evaluated — quantity is eroding loyalty, not reinforcing it."
    ),
    "female_customers_body": (
        "Female customers churn at 25.1% compared to 16.5% for males — a 52% higher rate. "
        "With 4,543 female customers in the portfolio, this segment alone accounts for 1,139 exits. "
        "Investigating whether product offerings, advisory quality, or service gaps drive this disparity is critical."
    ),
    "germany_body": (
        "Germany's churn rate is double that of France and Spain despite having a comparable customer base (2,509). "
        "With 814 departures, it accounts for 40% of all churn. This geographic concentration of attrition "
        "suggests systemic issues — potentially competitive pressure, pricing, or service model misalignment."
    ),
    "products_insight": (
        "<strong>Paradox alert:</strong> 2-product customers are the sweet spot at just <strong>7.6%</strong> churn. "
        "Beyond 2, every additional product dramatically increases exit probability. The cross-sell playbook needs a ceiling."
    ),
    "credit_score_insight": (
        "<strong>Observation:</strong> Credit score shows minimal correlation with churn — rates are relatively "
        "flat across bands (19.5%–23.7%). Churn is driven by <strong>engagement and product factors</strong>, not creditworthiness."
    ),
    "activity_balance_insight": (
        "<strong>Revenue risk:</strong> Customers with non-zero balances churn at <strong>24.1%</strong> — "
        "nearly double zero-balance customers. Avg churned balance is <strong>$91K</strong>, meaning each "
        "departure carries significant revenue implications."
    ),
    "tenure_insight": (
        "<strong>Observation:</strong> Tenure shows <strong>no meaningful protective effect</strong> against churn. "
        "Rates hover between 17–23% regardless of years with the bank. Loyalty programmes tied to tenure alone "
        "will not move the needle — the root causes lie elsewhere."
    ),
    "strategic_recommendations": (
        "<strong>Immediate priorities:</strong> (1) Investigate and address the <strong>Germany churn crisis</strong> — "
        "814 departures at 32.4% demand a regional intervention. (2) <strong>Cap cross-sell at 2 products</strong> — "
        "the data unequivocally shows that 3+ products accelerate churn. (3) Launch targeted "
        "<strong>re-engagement campaigns for inactive members</strong>, prioritising the 40–59 age band where "
        "churn peaks at 30–56%. (4) Address the <strong>gender gap</strong> in retention: female churn at 25.1% "
        "vs. 16.5% male warrants service experience analysis. (5) Protect <strong>high-balance customers</strong> — "
        "churned customers carry $91K average balances representing disproportionate revenue loss per departure."
    ),
    # Section subtitle
    "section_subtitle": (
        "Comprehensive analysis of customer attrition across demographics, products, and engagement. "
        "Based on 10,000 customer records."
    ),
    # Grantee card titles (user-editable labels)
    "grantee_title_inactive": "Inactive Members",
    "grantee_title_multiproduct": "Multi-Product Holders (3+)",
    "grantee_title_female": "Female Customers",
    "grantee_title_germany": "Germany Region",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# Sections that are user-editable labels only — AI never regenerates these.
_STATIC_SECTIONS = {
    "grantee_title_inactive",
    "grantee_title_multiproduct",
    "grantee_title_female",
    "grantee_title_germany",
}


def load_store() -> dict:
    if STORE_PATH.exists():
        with open(STORE_PATH) as f:
            store = json.load(f)
        # Add any new sections introduced after the store was first created
        changed = False
        for sid in SECTION_IDS:
            if sid not in store:
                store[sid] = {
                    "ai_generated_content": DEFAULT_COMMENTARY.get(sid, ""),
                    "user_overridden_content": None,
                    "is_user_override_active": False,
                    "last_data_refresh": _now(),
                    "last_override_at": None,
                }
                changed = True
        if changed:
            _save_store(store)
        return store
    store = {
        sid: {
            "ai_generated_content": DEFAULT_COMMENTARY.get(sid, ""),
            "user_overridden_content": None,
            "is_user_override_active": False,
            "last_data_refresh": _now(),
            "last_override_at": None,
        }
        for sid in SECTION_IDS
    }
    _save_store(store)
    return store


def _save_store(store: dict) -> None:
    with open(STORE_PATH, "w") as f:
        json.dump(store, f, indent=2)


def _with_active(store: dict) -> dict:
    out = {}
    for sid, data in store.items():
        out[sid] = {
            **data,
            "active_content": (
                data["user_overridden_content"]
                if data["is_user_override_active"]
                else data["ai_generated_content"]
            ),
        }
    return out


def get_all_commentary() -> dict:
    return _with_active(load_store())


def save_user_override(section_id: str, content: str) -> dict:
    store = load_store()
    if section_id not in store:
        raise ValueError(f"Unknown section: {section_id}")
    store[section_id]["user_overridden_content"] = content
    store[section_id]["is_user_override_active"] = True
    store[section_id]["last_override_at"] = _now()
    _save_store(store)
    return {**store[section_id], "active_content": content}


def clear_user_override(section_id: str) -> dict:
    store = load_store()
    if section_id not in store:
        raise ValueError(f"Unknown section: {section_id}")
    store[section_id]["is_user_override_active"] = False
    _save_store(store)
    ai_content = store[section_id]["ai_generated_content"]
    return {**store[section_id], "active_content": ai_content}


def _build_prompt(section_id: str, m: dict) -> str | None:
    # Static label sections are never AI-regenerated
    if section_id in _STATIC_SECTIONS:
        return None

    kpis = m["kpis"]
    geo = m["geography"]
    age = m["age"]
    gender = m["gender"]
    products = m["products"]
    activity = m["activity"]
    balance = m["balance"]
    cs = m["credit_score"]
    tenure = m["tenure"]

    base = (
        "You are a data analyst writing commentary for an executive bank churn dashboard. "
        "Use <strong> HTML tags to emphasise key numbers and percentages. "
        "Return only the commentary text — no markdown, no bullet prefixes on single sentences, "
        "no extra labels or explanations.\n\n"
    )

    if section_id == "section_subtitle":
        return base + (
            f"Write 1 concise sentence (max 20 words) summarising what this dashboard analyses. "
            f"Data source: {kpis['total_customers']:,} bank customer records including churn outcomes. "
            f"Do not mention specific churn numbers — this is a subtitle, not an insight."
        )

    if section_id == "executive_summary":
        return base + (
            f"Write 3 flowing sentences summarising the overall churn situation. Be specific with numbers.\n"
            f"- Total customers: {kpis['total_customers']:,}, Churned: {kpis['churned_customers']:,} ({kpis['churn_rate']}%)\n"
            f"- Germany: {geo['Germany']['churn_rate']}% vs France: {geo['France']['churn_rate']}%, Spain: {geo['Spain']['churn_rate']}%\n"
            f"- Female churn: {gender['Female']['churn_rate']}%, Male: {gender['Male']['churn_rate']}%\n"
            f"- 3-product: {products.get('3',{}).get('churn_rate','N/A')}%, 4-product: {products.get('4',{}).get('churn_rate','N/A')}%\n"
            f"- Inactive: {activity['Inactive']['churn_rate']}% vs Active: {activity['Active']['churn_rate']}%\n"
            f"- Avg churned balance: ${kpis['avg_balance_churned']:,.0f}"
        )

    if section_id == "geography_insight":
        g_pct_of_churn = round(geo['Germany']['churned'] / kpis['churned_customers'] * 100, 0)
        g_pct_of_customers = round(geo['Germany']['total'] / kpis['total_customers'] * 100, 0)
        return base + (
            f"Write 1 key insight sentence for the geography churn chart.\n"
            f"Germany: {geo['Germany']['total']:,} customers ({g_pct_of_customers:.0f}% of portfolio), "
            f"{geo['Germany']['churned']:,} churned ({g_pct_of_churn:.0f}% of all churned customers).\n"
            f"France: {geo['France']['churn_rate']}%, Spain: {geo['Spain']['churn_rate']}%, Germany: {geo['Germany']['churn_rate']}%."
        )

    if section_id == "age_insight":
        max_group = max(age.items(), key=lambda x: x[1]["churn_rate"])
        age_rates_str = ", ".join(f"{k}: {v['churn_rate']}%" for k, v in age.items())
        return base + (
            f"Write 2 sentences about the age distribution of churn.\n"
            f"Age churn rates: {age_rates_str}.\n"
            f"Highest-risk group: {max_group[0]} at {max_group[1]['churn_rate']}%."
        )

    if section_id == "inactive_members_body":
        ratio = round(activity["Inactive"]["churn_rate"] / activity["Active"]["churn_rate"], 1)
        return base + (
            f"Write 2 sentences about inactive member churn risk for a grantee-style card.\n"
            f"Inactive: {activity['Inactive']['total']:,} customers, {activity['Inactive']['churned']:,} churned at {activity['Inactive']['churn_rate']}%.\n"
            f"Active churn rate: {activity['Active']['churn_rate']}% — inactive is {ratio}x higher."
        )

    if section_id == "multi_product_body":
        return base + (
            f"Write 2 sentences about the multi-product churn paradox.\n"
            f"Product churn rates: 1={products.get('1',{}).get('churn_rate')}%, "
            f"2={products.get('2',{}).get('churn_rate')}%, "
            f"3={products.get('3',{}).get('churn_rate')}%, "
            f"4={products.get('4',{}).get('churn_rate')}%."
        )

    if section_id == "female_customers_body":
        ratio = round(gender["Female"]["churn_rate"] / gender["Male"]["churn_rate"], 1)
        return base + (
            f"Write 2 sentences about the gender churn gap.\n"
            f"Female: {gender['Female']['total']:,} customers, {gender['Female']['churned']:,} churned ({gender['Female']['churn_rate']}%).\n"
            f"Male: {gender['Male']['total']:,} customers, {gender['Male']['churned']:,} churned ({gender['Male']['churn_rate']}%). Ratio: {ratio}x."
        )

    if section_id == "germany_body":
        return base + (
            f"Write 2 sentences about Germany's outsized churn for a risk card.\n"
            f"Germany: {geo['Germany']['total']:,} customers, {geo['Germany']['churned']:,} churned ({geo['Germany']['churn_rate']}%).\n"
            f"France: {geo['France']['churn_rate']}%, Spain: {geo['Spain']['churn_rate']}%."
        )

    if section_id == "products_insight":
        return base + (
            f"Write 1 sentence highlighting the product churn paradox.\n"
            f"Churn rates: 1 product={products.get('1',{}).get('churn_rate')}%, "
            f"2 products={products.get('2',{}).get('churn_rate')}%, "
            f"3 products={products.get('3',{}).get('churn_rate')}%, "
            f"4 products={products.get('4',{}).get('churn_rate')}%."
        )

    if section_id == "credit_score_insight":
        rates = [v["churn_rate"] for v in cs.values()]
        cs_rates_str = ", ".join(f"{k}: {v['churn_rate']}%" for k, v in cs.items())
        return base + (
            f"Write 1 observation sentence about credit score and churn.\n"
            f"Credit score churn rates: {cs_rates_str}.\n"
            f"Range: {min(rates)}%–{max(rates)}%."
        )

    if section_id == "activity_balance_insight":
        return base + (
            f"Write 1-2 sentences about the revenue risk of balance-holding customers churning.\n"
            f"Zero-balance churn: {balance['Zero Balance']['churn_rate']}%, Has-balance churn: {balance['Has Balance']['churn_rate']}%.\n"
            f"Avg churned balance: ${kpis['avg_balance_churned']:,.0f}, avg retained: ${kpis['avg_balance_retained']:,.0f}."
        )

    if section_id == "tenure_insight":
        rates = [v["churn_rate"] for v in tenure.values()]
        tenure_rates_str = ", ".join(f"yr{k}={v['churn_rate']}%" for k, v in tenure.items())
        return base + (
            f"Write 1 observation sentence about tenure and its lack of protective effect on churn.\n"
            f"Tenure churn rates (yr 0–10): {tenure_rates_str}.\n"
            f"Range: {min(rates)}%–{max(rates)}%."
        )

    if section_id == "strategic_recommendations":
        return base + (
            f"Write 4-5 numbered strategic recommendations for a bank executive based on these churn insights. "
            f"Format as flowing HTML with <strong> emphasis on key numbers. Keep each point punchy — 1 sentence each.\n"
            f"- Overall churn: {kpis['churn_rate']}% ({kpis['churned_customers']:,} customers)\n"
            f"- Germany crisis: {geo['Germany']['churn_rate']}% churn\n"
            f"- Product paradox: 2-product ({products.get('2',{}).get('churn_rate')}%) is optimal, "
            f"3+ ({products.get('3',{}).get('churn_rate',0)}%+) is catastrophic\n"
            f"- Inactive members: {activity['Inactive']['churn_rate']}% churn\n"
            f"- Female customers: {gender['Female']['churn_rate']}% vs male {gender['Male']['churn_rate']}%\n"
            f"- High-balance churn risk: ${kpis['avg_balance_churned']:,.0f} avg balance"
        )

    return base + "Write 2 sentences of data commentary."


def regenerate_all(skip_overridden: bool = True) -> dict:
    """Re-read Excel, recompute metrics, regenerate AI commentary for non-overridden sections."""
    metrics = compute_metrics()
    store = load_store()
    now = _now()
    errors = []

    for sid in SECTION_IDS:
        if skip_overridden and store.get(sid, {}).get("is_user_override_active"):
            continue
        prompt = _build_prompt(sid, metrics)
        if prompt is None:
            continue  # Static label — skip AI generation
        try:
            content = generate_commentary(prompt)
            store[sid]["ai_generated_content"] = content
            store[sid]["last_data_refresh"] = now
        except Exception as e:
            errors.append(f"{sid}: {str(e)}")

    _save_store(store)
    return {
        "commentary": _with_active(store),
        "metrics": metrics,
        "errors": errors,
    }
