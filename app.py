import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Bank Retention Analytics", page_icon="📊", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv('European_Bank.csv')
    df['HasCrCard'] = df['HasCrCard'].astype(int)
    df['IsActiveMember'] = df['IsActiveMember'].astype(int)
    df['Exited'] = df['Exited'].astype(int)
    df['Age'] = df['Age'].clip(18, 100)
    df['CreditScore'] = df['CreditScore'].clip(300, 850)
    
    balance_median = df['Balance'].median()
    df['Engagement_Profile'] = 'Other'
    df.loc[df['IsActiveMember'] == 1, 'Engagement_Profile'] = 'Active Engaged'
    df.loc[df['IsActiveMember'] == 0, 'Engagement_Profile'] = 'Inactive Disengaged'
    df.loc[(df['IsActiveMember'] == 1) & (df['NumOfProducts'] <= 2), 'Engagement_Profile'] = 'Active, Low Product'
    df.loc[(df['IsActiveMember'] == 0) & (df['Balance'] > balance_median), 'Engagement_Profile'] = 'Inactive, High Balance'
    
    max_tenure = df['Tenure'].max()
    df['Tenure_Score'] = df['Tenure'] / max_tenure if max_tenure > 0 else 0
    df['Activeness_Score'] = df['IsActiveMember']
    df['Product_Score'] = df['NumOfProducts'] / 4
    df['Relationship_Strength_Index'] = (df['Tenure_Score'] + df['Activeness_Score'] + df['Product_Score']) / 3
    return df

df = load_data()

st.sidebar.header("🔍 Filter Customers")
selected_profile = st.sidebar.selectbox("Engagement Profile", ['All'] + sorted(df['Engagement_Profile'].unique()))
min_products = st.sidebar.slider("Min Products", 1, 4, 1)
max_products = st.sidebar.slider("Max Products", 1, 4, 4)
min_balance = st.sidebar.number_input("Min Balance (€)", 0, int(df['Balance'].max()), 0)
max_balance = st.sidebar.number_input("Max Balance (€)", 0, int(df['Balance'].max()), int(df['Balance'].max()))

filtered_df = df.copy()
if selected_profile != 'All':
    filtered_df = filtered_df[filtered_df['Engagement_Profile'] == selected_profile]
filtered_df = filtered_df[(filtered_df['NumOfProducts'] >= min_products) & (filtered_df['NumOfProducts'] <= max_products)]
filtered_df = filtered_df[(filtered_df['Balance'] >= min_balance) & (filtered_df['Balance'] <= max_balance)]

st.sidebar.markdown(f"**Showing {len(filtered_df):,} customers**")

st.title("🏦 Customer Engagement & Retention Dashboard")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Overall Churn", f"{df['Exited'].mean()*100:.1f}%")
with col2:
    st.metric("Active Members", f"{df[df['IsActiveMember']==1]['Exited'].mean()*100:.1f}%")
with col3:
    st.metric("Inactive Members", f"{df[df['IsActiveMember']==0]['Exited'].mean()*100:.1f}%")
with col4:
    st.metric("Avg Relationship Strength", f"{df['Relationship_Strength_Index'].mean():.2f}")

if not filtered_df.empty:
    engagement_churn = filtered_df.groupby('Engagement_Profile')['Exited'].mean().reset_index()
    engagement_churn['Churn Rate (%)'] = engagement_churn['Exited'] * 100
    fig1 = px.bar(engagement_churn, x='Engagement_Profile', y='Churn Rate (%)', color='Churn Rate (%)', text_auto='.1f')
    st.plotly_chart(fig1, use_container_width=True)
    
    prod_churn = filtered_df.groupby('NumOfProducts')['Exited'].mean().reset_index()
    prod_churn['Churn Rate (%)'] = prod_churn['Exited'] * 100
    fig2 = px.line(prod_churn, x='NumOfProducts', y='Churn Rate (%)', markers=True)
    st.plotly_chart(fig2, use_container_width=True)
    
    st.subheader("⚠️ At‑Risk Premium Customers")
    balance_80th = df['Balance'].quantile(0.8)
    high_balance_inactive = filtered_df[(filtered_df['Balance'] > balance_80th) & (filtered_df['IsActiveMember'] == 0)]
    if not high_balance_inactive.empty:
        st.warning(f"**{len(high_balance_inactive)}** high‑balance inactive customers identified.")
        st.dataframe(high_balance_inactive[['CustomerId', 'Balance', 'NumOfProducts', 'Tenure']].head(10))
    else:
        st.info("No high‑balance inactive customers.")
    
    st.subheader("💪 Retention Strength")
    fig4 = px.histogram(filtered_df, x='Relationship_Strength_Index', nbins=30)
    st.plotly_chart(fig4, use_container_width=True)
    
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download filtered data", csv, "filtered_customers.csv", "text/csv")
else:
    st.warning("No customers match the current filters.")



