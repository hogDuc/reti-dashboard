import pandas as pd
import streamlit as st
from pandas.tseries.offsets import MonthEnd
import numpy as np

# Shorten unit
UNIT = 1000000

# Process data

def readData(sheetName="", valueName=""):
    data = pd.read_excel("reti_data.xlsx", sheet_name=sheetName, header=None).transpose()
    data.columns = data.iloc[0]
    data = data[1:]
    df = pd.melt(
        data,
        id_vars=['Tháng',"Năm"],
        value_vars=data.columns[2:],
        var_name="project",
        value_name=valueName
    ).rename(columns={
        "Tháng":"month",
        "Năm":"year"
    }).assign(
        date=lambda x: x['month'].astype(int).astype(str) + '/' + x['year'].astype(int).astype(str)
    ).assign(
        date = lambda x: pd.to_datetime(x['date'], format="%m/%Y") + MonthEnd(0)
    )
    return df

revenue_df = readData('revenue', 'revenue')
cogs_df = readData('cogs', 'cogs')
revenue_df["project"] = revenue_df["project"].replace("DOANH THU", "total")
cogs_df["project"] = cogs_df["project"].replace("GIÁ VỐN HÀNG BÁN", "total")
df = pd.merge(revenue_df, cogs_df, how='outer', on=["project", "date", "year", "month"]).assign(
    CoR = lambda x: x["cogs"] / x["revenue"].replace(0, np.nan)
)

st.set_page_config(
    layout="wide"
)
st.header("RETI Dashboard")
<<<<<<< HEAD

metric_1, metric_2, metric_3, metric_4 = st.columns(4)
with metric_1:
    st.metric(
        label="Total revenue 2024 (Million VND)",
        # value="test"
        value= round(sum(df.loc[(df["project"]=="total") & (df['year']==2024)]["revenue"])/UNIT, 2)
        # value = round(np.nansum(df.loc[~df.project.isin(["DOANH THU"])].loc[df['year']==2024]["revenue"])/1000000 ,2)
    )
with metric_2:
    st.metric(
        label="Last reported monthly total revenue (Million VND)",
        value=round(df.sort_values(by=["year", "month"]).loc[df["project"]=="total"]["revenue"].tail(1).values[0] / UNIT,2),
        delta=round(df.sort_values(by=["year", "month"]).loc[df["project"]=="total"]["revenue"].diff(periods=12).tail(1).values[0] / UNIT , 2)
    )   
with metric_3:
    st.metric(
        label="COGS/Revenue",
        value=round(df.sort_values(by=["year", "month"]).loc[df["project"]=="total"]["CoR"].tail(1).values[0],2),
        delta=round(df.sort_values(by=["year", "month"]).loc[df["project"]=="total"]["CoR"].diff(periods=12).tail(1).values[0], 2)
    )
# with metric_4:
#     st.metric("metric 4")


st.bar_chart(
    data=df,
    x="date",
    y="revenue",
    color="project",
    stack=False
)
