import streamlit as st
import os
from openai import OpenAI

client = OpenAI(
  api_key=os.environ.get("OPENAI_API_KEY"),
)

st.set_page_config(page_title="Financial Planning Assistant", layout="wide")

st.title("Client Financial Planning Assistant")
st.caption("Generate a high‑level financial plan outline you can refine and deliver.")

# ---------------- Sidebar Inputs ---------------- #
with st.sidebar:
    st.header("Client Basics")
    age = st.number_input("Age", 18, 100, 35)
    kids = st.number_input("Children", 0, 10, 0)
    marital_status = st.selectbox("Marital Status", ["Single", "Married", "Divorced", "Widowed"])

    st.header("Cash Flow & Net Worth")
    income = st.number_input("Annual Income ($)", 0, step=1000, format="%d")
    expenses = st.number_input("Annual Expenses ($)", 0, step=1000, format="%d")
    assets = st.number_input("Investable Assets ($)", 0, step=1000, format="%d")
    liabilities = st.number_input("Total Liabilities ($)", 0, step=1000, format="%d")

    st.header("Risk & Horizon")
    risk_tolerance = st.selectbox("Risk Tolerance", ["Low", "Moderate", "High"])
    volatility_pref = st.selectbox("Volatility Comfort", ["Low", "Average", "High"])
    time_horizon_years = st.slider("Primary Time Horizon (years)", 1, 40, 15)

    st.header("Health & Insurance")
    smoker = st.selectbox("Smoker?", ["No", "Yes"])
    health_status = st.selectbox("Overall Health", ["Excellent", "Good", "Fair", "Poor"])

    st.header("Goals")
    goals = st.multiselect("Select Goals", [
        "Retirement",
        "Major Purchases",
        "Children's Education",
        "Debt Repayment",
        "Wealth Accumulation",
        "Specific Investments",
        "Estate / Legacy Planning",
        "Tax Planning"
    ])

    st.header("Custom Advisor Notes")
    custom_notes = st.text_area("Add any custom client preferences or holdings (e.g. must keep ABC ETF).")

    st.header("AI Draft")
    use_ai = st.checkbox("Generate AI‑assisted narrative (requires OpenAI API key)")

# --------------- Helper Functions --------------- #

def recommend_portfolio(risk: str, include_insurance: bool = True):
    """Return allocation dict based on risk tolerance."""
    if risk == "Low":
        base = {
            "Bonds": 40,
            "Large Cap Stocks": 20,
            "International Stocks": 10,
            "REITs": 10,
            "Cash": 10,
        }
    elif risk == "Moderate":
        base = {
            "Large Cap Stocks": 25,
            "Mid Cap Stocks": 15,
            "International Stocks": 20,
            "Bonds": 20,
            "Alternatives": 10,
            "Cash": 10,
        }
    else:  # High
        base = {
            "Growth Stocks": 30,
            "Small Cap Stocks": 20,
            "International Stocks": 20,
            "Crypto": 10,
            "Bonds": 10,
            "Alternatives": 10,
        }

    if include_insurance:
        reserve = 5  # percent for insurance premiums
        base["Life Insurance Premium Reserve"] = reserve
        scale = (100 - reserve) / (sum(base.values()) - reserve)
        for k in list(base.keys()):
            if k != "Life Insurance Premium Reserve":
                base[k] = round(base[k] * scale, 1)

    return base


def recommend_insurance(age: int, smoker: str, health: str, income: float, risk: str):
    """Return tuple of (product type, coverage amount)."""
    base_need = income * 10  # simple rule of thumb
    if age > 50:
        base_need *= 0.75

    if smoker == "Yes" or health in ("Fair", "Poor"):
        product = "Term Life (focus on affordability)"
    elif age < 45:
        product = "Term Life with convertible option"
    elif risk == "High":
        product = "Variable Universal Life"
    else:
        product = "Whole Life"

    return product, int(base_need)


def recommend_vehicles(age: int, income: float, kids: int):
    vehicles = []
    if age < 50:
        vehicles.append("Roth IRA")
    if income < 155000:
        vehicles.append("Traditional IRA")
    if income > 155000:
        vehicles.append("Backdoor Roth")
    vehicles.append("401(k) / 403(b)")
    if age > 55:
        vehicles.append("Deferred or Immediate Annuity")
    if kids > 0:
        vehicles.append("529 Plan")
    vehicles.append("HSA (if eligible)")
    return vehicles


def get_ai_plan(context: str):
    """Call OpenAI API to create a narrative plan."""
    try:
        import openai

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "OpenAI API key not found in environment."
        openai.api_key = api_key

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a CFP® producing concise, compliant financial plans."},
                {"role": "user", "content": context},
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"AI generation error: {e}"


# --------------- Generate Plan --------------- #
if st.button("Generate Plan"):
    st.subheader("Client Snapshot")
    st.markdown(
        f"- **Age**: {age}\n"
        f"- **Marital Status**: {marital_status}\n"
        f"- **Children**: {kids}\n"
        f"- **Goals**: {', '.join(goals) if goals else 'None specified'}"
    )

    st.subheader("Net Worth & Cash Flow")
    st.markdown(
        f"- **Income**: ${income:,.0f}\n"
        f"- **Expenses**: ${expenses:,.0f}\n"
        f"- **Assets**: ${assets:,.0f}\n"
        f"- **Liabilities**: ${liabilities:,.0f}"
    )

    st.subheader("Recommended Portfolio Allocation")
    allocation = recommend_portfolio(risk_tolerance)
    for category, percent in allocation.items():
        st.markdown(f"* {category}: {percent}%")

    st.subheader("Life Insurance Recommendation")
    product, coverage = recommend_insurance(age, smoker, health_status, income, risk_tolerance)
    st.markdown(
        f"- **Product Type**: {product}\n"
        f"- **Suggested Coverage**: ${coverage:,.0f}"
    )

    st.subheader("Retirement & Investment Vehicles")
    for v in recommend_vehicles(age, income, kids):
        st.markdown(f"- {v}")

    st.subheader("Custom Advisor Recommendations")
    st.markdown(custom_notes if custom_notes else "_None provided_")

    if use_ai:
        st.subheader("AI‑Generated Narrative Plan")
        context = (
            f"Client age {age}, {kids} kids, {marital_status}, "
            f"income {income}, assets {assets}, liabilities {liabilities}, expenses {expenses}, "
            f"risk {risk_tolerance}, volatility {volatility_pref}, horizon {time_horizon_years} years, "
            f"health {health_status}, smoker {smoker}, goals {goals}, advisor notes: {custom_notes}. "
            "Generate a concise, client‑friendly financial plan outline."
        )
        st.write(get_ai_plan(context))

    st.info("All recommendations are illustrative and should be validated for suitability, tax impact, and regulatory compliance.")
