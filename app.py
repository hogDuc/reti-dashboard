import pandas as pd
import streamlit as st
# import matplotlib.pyplot as plt

# Read data
revenue_df = pd.read_excel("reti_data.xlsx", sheet_name="revenue", header=None)

st.header("RETI Dashboard")
st.dataframe(revenue_df)
