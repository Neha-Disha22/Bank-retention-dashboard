import streamlit as st 
import pandas as pd 
import plotly.express as px 
st.set_page_config(page_title="Bank Retention", layout="wide") 
@st.cache_data 
def load_data(): 
    df = pd.read_csv("European_Bank.csv") 
    df["Exited"] = df["Exited"].astype(int) 
    return df 
df = load_data() 
st.title("Customer Churn Dashboard") 
col1, col2, col3 = st.columns(3) 
col1.metric("Overall Churn", f"{df['Exited'].mean()*100:.1f}%%") 
col2.metric("Active Members", f"{df[df['IsActiveMember']==1]['Exited'].mean()*100:.1f}%%") 
col3.metric("Inactive Members", f"{df[df['IsActiveMember']==0]['Exited'].mean()*100:.1f}%%") 
fig = px.histogram(df, x="Age", color="Exited", barmode="overlay") 
