import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

# Configure page
st.set_page_config(
    page_title="Finance Analytics",
    page_icon="💰",
    layout="wide"
)

st.title("Finance Analytics Dashboard")

# Fetch data from Flask API
@st.cache_data(ttl=300)
def get_finance_data():
    try:
        response = requests.get("http://localhost:5000/api/finance-data", timeout=10)
        if response.status_code == 200:
            return response.json()
        st.error(f"API Error: Status {response.status_code}")
        return None
    except Exception as e:
        st.error(f"Connection Error: {str(e)}")
        return None

data = get_finance_data()

# Debug output
st.write("API Response Sample:", {k: v[:2] if isinstance(v, list) else v for k, v in data.items()} if data else "No data")

if not data:
    st.error("Failed to load data from API")
    st.stop()

# Process data with error handling
try:
    transactions = pd.DataFrame(data.get('transactions', []))
    budgets = pd.DataFrame(data.get('budgets', []))
    
    if transactions.empty:
        st.warning("No transactions data available")
    if budgets.empty:
        st.warning("No budgets data available")
        
    # Add derived columns
    transactions['type'] = transactions['amount'].apply(
        lambda x: 'Income' if x > 0 else 'Expense'
    )
    transactions['amount_abs'] = transactions['amount'].abs()
    transactions['date'] = pd.to_datetime(transactions['date'])
    transactions['month'] = transactions['date'].dt.to_period('M').astype(str)

except Exception as e:
    st.error(f"Data processing failed: {str(e)}")
    st.stop()

# Dashboard layout
tab1, tab2, tab3 = st.tabs(["Overview", "Budgets", "Raw Data"])

with tab1:
    st.header("Financial Overview")
    
    if transactions.empty:
        st.warning("No transactions to display")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Monthly Trends")
            monthly_data = transactions.groupby(['month', 'type'])['amount_abs'].sum().unstack()
            fig = px.line(
                monthly_data.reset_index(),
                x='month',
                y=['Income', 'Expense'],
                labels={'value': 'Amount ($)', 'month': 'Month'},
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Category Breakdown")
            fig = px.sunburst(
                transactions.groupby(['type', 'category'])['amount_abs'].sum().reset_index(),
                path=['type', 'category'],
                values='amount_abs',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("Budget Analysis")
    
    if budgets.empty:
        st.warning("No budget data available")
    else:
        spending = transactions[transactions['type'] == 'Expense']
        budget_analysis = pd.merge(
            budgets,
            spending.groupby('category')['amount_abs'].sum().reset_index(),
            on='category',
            how='left'
        ).fillna(0)
        
        budget_analysis['utilization'] = (budget_analysis['amount_abs'] / budget_analysis['limit_amount']) * 100
        budget_analysis['status'] = budget_analysis['utilization'].apply(
            lambda x: 'Over' if x > 100 else ('Near' if x > 80 else 'Under')
        )
        
        st.subheader("Budget Status")
        fig = px.bar(
            budget_analysis,
            x='category',
            y='utilization',
            color='status',
            color_discrete_map={
                'Under': '#2ecc71',
                'Near': '#f39c12',
                'Over': '#e74c3c'
            },
            labels={'utilization': 'Budget Utilization (%)', 'category': 'Category'},
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Budget Details")
        st.dataframe(
            budget_analysis[[
                'category', 'limit_amount', 'amount_abs', 'utilization'
            ]].rename(columns={
                'category': 'Category',
                'limit_amount': 'Budget Limit',
                'amount_abs': 'Actual Spending',
                'utilization': 'Utilization %'
            }),
            use_container_width=True
        )

with tab3:
    st.header("Transaction Data")
    if transactions.empty:
        st.warning("No transactions to display")
    else:
        st.dataframe(
            transactions[['date', 'category', 'amount', 'description']].rename(columns={
                'date': 'Date',
                'category': 'Category',
                'amount': 'Amount',
                'description': 'Description'
            }),
            use_container_width=True
        )