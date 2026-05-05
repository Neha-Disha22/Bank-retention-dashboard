# app.py
# Customer Engagement & Product Utilization Analytics – Complete Dashboard

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')
# ================== PAGE CONFIG ==================
st.set_page_config(page_title="Bank Retention Analytics", page_icon="📊", layout="wide")

# ================== LOAD DATA WITH CACHING ==================
@st.cache_data
def load_data():
    df = pd.read_csv('European_Bank.csv')
    
    # Data cleaning
    df['HasCrCard'] = df['HasCrCard'].astype(int)
    df['IsActiveMember'] = df['IsActiveMember'].astype(int)
    df['Exited'] = df['Exited'].astype(int)
    df['Age'] = df['Age'].clip(18, 100)
    df['CreditScore'] = df['CreditScore'].clip(300, 850)
    
    # Engagement profiles
    balance_median = df['Balance'].median()
    df['Engagement_Profile'] = 'Other'
    df.loc[df['IsActiveMember'] == 1, 'Engagement_Profile'] = 'Active Engaged'
    df.loc[df['IsActiveMember'] == 0, 'Engagement_Profile'] = 'Inactive Disengaged'
    df.loc[(df['IsActiveMember'] == 1) & (df['NumOfProducts'] <= 2), 'Engagement_Profile'] = 'Active, Low Product'
    df.loc[(df['IsActiveMember'] == 0) & (df['Balance'] > balance_median), 'Engagement_Profile'] = 'Inactive, High Balance'
    
    # Relationship Strength Index
    max_tenure = df['Tenure'].max()
    df['Tenure_Score'] = df['Tenure'] / max_tenure if max_tenure > 0 else 0
    df['Activeness_Score'] = df['IsActiveMember']
    df['Product_Score'] = df['NumOfProducts'] / 4
    df['Relationship_Strength_Index'] = (df['Tenure_Score'] + df['Activeness_Score'] + df['Product_Score']) / 3
    
    return df

df = load_data()

# ================== SIDEBAR FILTERS ==================
st.sidebar.header("🔍 Filter Customers")
engagement_options = ['All'] + sorted(df['Engagement_Profile'].unique())
selected_profile = st.sidebar.selectbox("Engagement Profile", engagement_options)

min_products = st.sidebar.slider("Minimum Number of Products", 1, 4, 1)
max_products = st.sidebar.slider("Maximum Number of Products", 1, 4, 4)

min_balance = st.sidebar.number_input("Min Balance (€)", value=0, step=1000)
max_balance = st.sidebar.number_input("Max Balance (€)", value=int(df['Balance'].max()), step=5000)

min_salary = st.sidebar.number_input("Min Estimated Salary (€)", value=0, step=5000)
max_salary = st.sidebar.number_input("Max Estimated Salary (€)", value=int(df['EstimatedSalary'].max()), step=5000)

# Apply filters
filtered_df = df.copy()
if selected_profile != 'All':
    filtered_df = filtered_df[filtered_df['Engagement_Profile'] == selected_profile]
filtered_df = filtered_df[(filtered_df['NumOfProducts'] >= min_products) & (filtered_df['NumOfProducts'] <= max_products)]
filtered_df = filtered_df[(filtered_df['Balance'] >= min_balance) & (filtered_df['Balance'] <= max_balance)]
filtered_df = filtered_df[(filtered_df['EstimatedSalary'] >= min_salary) & (filtered_df['EstimatedSalary'] <= max_salary)]

st.sidebar.markdown(f"**Showing {len(filtered_df):,} customers** (out of {len(df):,})")

# ================== MAIN DASHBOARD ==================
st.title("🏦 Customer Engagement & Retention Dashboard")
st.markdown("### Analyze churn drivers through behavioral and relationship lenses")

# ---- Row 1: KPI Cards ----
col1, col2, col3, col4 = st.columns(4)
with col1:
    overall_churn = df['Exited'].mean() * 100
    st.metric("Overall Churn Rate", f"{overall_churn:.1f}%")
with col2:
    active_churn = df[df['IsActiveMember']==1]['Exited'].mean() * 100
    st.metric("Active Members Churn", f"{active_churn:.1f}%")
with col3:
    inactive_churn = df[df['IsActiveMember']==0]['Exited'].mean() * 100
    st.metric("Inactive Members Churn", f"{inactive_churn:.1f}%")
with col4:
    avg_relationship = df['Relationship_Strength_Index'].mean()
    st.metric("Avg Relationship Strength", f"{avg_relationship:.2f}")

# ---- Row 2: Engagement Profile vs Churn ----
st.subheader("📌 Engagement Profile & Churn")
if filtered_df.empty:
    st.warning("No customers match the current filters.")
else:
    engagement_churn = filtered_df.groupby('Engagement_Profile')['Exited'].mean().reset_index()
    engagement_churn['Churn Rate (%)'] = engagement_churn['Exited'] * 100
    fig1 = px.bar(engagement_churn, x='Engagement_Profile', y='Churn Rate (%)',
                  color='Churn Rate (%)', text_auto='.1f',
                  title="Churn Rate by Engagement Profile")
    st.plotly_chart(fig1, width='stretch')

# ---- Row 3: Product Utilization Impact ----
st.subheader("📦 Product Utilization Impact")
prod_churn = filtered_df.groupby('NumOfProducts')['Exited'].mean().reset_index()
prod_churn['Churn Rate (%)'] = prod_churn['Exited'] * 100
fig2 = px.line(prod_churn, x='NumOfProducts', y='Churn Rate (%)', markers=True,
               title="Churn Rate vs Number of Products")
st.plotly_chart(fig2, width='stretch')

# Single vs multi-product insight
st.markdown("#### Single‑Product vs Multi‑Product Retention")
df['Product_Category'] = np.where(df['NumOfProducts'] == 1, 'Single-Product',
                                  np.where(df['NumOfProducts'] >= 3, 'Multi-Product (3+)', '2-Products'))
cat_churn = df.groupby('Product_Category')['Exited'].mean() * 100
cat_churn_df = cat_churn.reset_index()
cat_churn_df.columns = ['Product Category', 'Churn Rate (%)']
fig3 = px.bar(cat_churn_df, x='Product Category', y='Churn Rate (%)', text_auto='.1f',
              title="Churn Rate by Product Category")
st.plotly_chart(fig3, width='stretch')

# ---- Row 4: Credit Card & Activeness ----
st.markdown("#### Product Ownership & Retention")
prod_cat = filtered_df.groupby(['HasCrCard', 'IsActiveMember'])['Exited'].mean().reset_index()
prod_cat['Churn Rate (%)'] = prod_cat['Exited'] * 100
prod_cat['Segment'] = prod_cat.apply(lambda x: f"Card: {int(x['HasCrCard'])} / Active: {int(x['IsActiveMember'])}", axis=1)
fig4 = px.bar(prod_cat, x='Segment', y='Churn Rate (%)', text_auto='.1f',
              title="Churn by Credit Card Ownership and Activeness")
st.plotly_chart(fig4, width='stretch')

# ---- Row 5: High‑Value Disengaged Detector ----
st.subheader("⚠️ At‑Risk Premium Customers")
balance_80th = df['Balance'].quantile(0.8)
high_balance_inactive = filtered_df[(filtered_df['Balance'] > balance_80th) & (filtered_df['IsActiveMember'] == 0)]
if not high_balance_inactive.empty:
    st.warning(f"**{len(high_balance_inactive):,}** high‑balance (>€{balance_80th:,.0f}) but **inactive** customers identified.")
    st.dataframe(high_balance_inactive[['CustomerId', 'Balance', 'NumOfProducts', 'Tenure', 'EstimatedSalary']].head(10))
    st.caption("These customers have financial means but low engagement – ideal for retention campaigns.")
else:
    st.info("No high‑balance inactive customers in the current filtered set.")

# ---- Row 6: Relationship Strength Distribution ----
st.subheader("💪 Retention Strength Distribution")
if not filtered_df.empty:
    fig5 = px.histogram(filtered_df, x='Relationship_Strength_Index', nbins=30,
                        title="Distribution of Relationship Strength Index",
                        labels={'Relationship_Strength_Index': 'Strength Score'})
    retained_avg = filtered_df[filtered_df['Exited']==0]['Relationship_Strength_Index'].mean()
    churned_avg = filtered_df[filtered_df['Exited']==1]['Relationship_Strength_Index'].mean()
    fig5.add_vline(x=retained_avg, line_dash="dash", line_color="green", annotation_text=f"Retained avg: {retained_avg:.2f}")
    fig5.add_vline(x=churned_avg, line_dash="dash", line_color="red", annotation_text=f"Churned avg: {churned_avg:.2f}")
    st.plotly_chart(fig5, width='stretch')
else:
    st.info("No data for selected filters.")

# ---- Export Data ----
st.subheader("📥 Export Filtered Data")
csv = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button("Download filtered customers as CSV", csv, "filtered_customers.csv", "text/csv")

# ---- Footer ----
st.markdown("---")
st.caption("Dashboard built for European Bank Retention Analytics Project | Data-driven engagement & product utilization insights")
