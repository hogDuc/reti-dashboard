import pandas as pd
from pandas.tseries.offsets import MonthEnd
import plotly.express as px
import numpy as np
import streamlit as st
import os

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

def pct_change_abs(series, periods=1):
    """
    Calculate percent change using absolute value of the previous period.
    Allows specifying the number of periods to look back.

    Parameters:
    - series: pd.Series
    - periods: int, number of periods to shift (default=1)

    Returns:
    - pd.Series of percentage changes
    """
    prev = series.shift(periods)
    return (series - prev) / prev.abs()

revenue_df = readData('revenue', 'revenue')
cogs_df = readData('cogs', 'cogs')
fee_df = readData('fee', 'fee')
ebt_df = pd.DataFrame(
    fee_df.assign(
        year = lambda x: x['year'].astype(int),
        month = lambda x: x['month'].astype(int)
    ).loc[fee_df["project"] == "LỢI NHUẬN THUẦN TRƯỚC THUẾ"].groupby(["year","month"])["fee"].sum()
)

revenue_df.loc[:,"project"] = revenue_df["project"].replace("DOANH THU", "total")
cogs_df.loc[:,"project"] = cogs_df["project"].replace("GIÁ VỐN HÀNG BÁN", "total")

df = pd.merge(revenue_df, cogs_df, how='outer', on=["project", "date", "year", "month"]).assign(
    CoR = lambda x: x["cogs"] / x["revenue"].replace(0, np.nan)
).assign(
    month = lambda x: x['month'].astype(int),
    year = lambda x: x['year'].astype(int),
    revenue = lambda x: x['revenue'].astype(float),
    cogs = lambda x: x['cogs'].astype(float),
    CoR = lambda x: x['CoR'].astype(float),
)

ignore_category = [
    "DOANH THU", "Thưởng nóng", "Doanh thu cho thuê HCM",
    "Doanh thu khác", "Giá vốn VP HCM", "total"
]


revenue_df = df.loc[(~df.project.isin(ignore_category))]

project_df = revenue_df.groupby('project')[['revenue', 'cogs']].sum().reset_index()\
    .assign(
        grossProfit = lambda x: x["revenue"] - x["cogs"],
    ).assign(
        grossProfit = lambda x: x["grossProfit"].fillna(0),
        grossMargin = lambda x: x["grossProfit"] / x['revenue'].fillna(0),
        cogsOverRev = lambda x: x["cogs"] / x["revenue"].fillna(0)
    )

revenue_bar = px.bar(
    data_frame=project_df.sort_values(by="grossProfit", ascending=True), 
    x="grossProfit",
    orientation='h',
    y="project",
    title="Project Gross profit"
)
revenue_bar.update_layout(
    xaxis_title=None, 
    yaxis_title=None,
    plot_bgcolor =  "rgba(0, 0, 0, 0)",
    paper_bgcolor = "rgba(0, 0, 0, 0)",
    yaxis=dict(
        tickfont=dict(size=10)
    )
)
revenue_bar.update_traces(
    marker_color='#ee5a37',
    hovertemplate="<b>%{y}</b><br>Gross Profit: %{x:,.0f}<extra></extra>"
)

revenue_pie = px.pie(
    data_frame=revenue_df, 
    # x="date", 
    values="revenue",
    names="project",
    hole =.3,
    title = "Revenue components"
)
revenue_pie.update_layout(
    showlegend=False, 
    uniformtext_minsize = 12, 
    uniformtext_mode = 'hide',
    plot_bgcolor =  "rgba(0, 0, 0, 0)",
    paper_bgcolor = "rgba(0, 0, 0, 0)",
)
revenue_pie.update_traces(
    textposition='inside',
    hovertemplate="<b>%{label}</b><br>Revenue: %{value:,.0f}<extra></extra>"
)

# Overall Business metrics
reti_overall = df.loc[~(df.project.isin(["total"]))]\
    .groupby(['year', 'month'])[['revenue', 'cogs']].sum()\
    .assign(
        grossProfit = lambda x: x["revenue"] - x["cogs"],
        # changeRevenue = lambda x: x['revenue'].pct_change(periods=12)*100,
        changeRevenue = lambda x: pct_change_abs(x['revenue'], periods=12)*100,
        # changeCogs = lambda x: x['cogs'].pct_change(periods=12),
        changeCogs =lambda x: pct_change_abs(x['cogs'], periods=12),
        # changeGrossProfit = lambda x: x['grossProfit'].pct_change(periods=12)*100,
        changeGrossProfit =lambda x: pct_change_abs(x['grossProfit'], periods=12)*100,
        profitMargin = lambda x: x["grossProfit"] / x["revenue"].replace(0, np.nan),
        changeProfitMargin = lambda x: x["profitMargin"].diff(periods=12)
    )
reti_overall = pd.merge(reti_overall, ebt_df, on=["year", "month"])\
    .rename(columns={"fee":"ebt"})\
    .assign(
        ebtMargin = lambda x: x["ebt"] / x["revenue"].replace(0, np.nan),
        changeEbtMargin = lambda x: x["ebtMargin"].diff(periods=12)
    )

# Separate revenue sources
other_revenue = pd.DataFrame(
    df.loc[(df.project.isin(["Doanh thu cho thuê HCM", "Thưởng nóng"]))].groupby(["year", "month", "project"])[["revenue"]].sum()
).reset_index()
operational_revenue = pd.DataFrame(revenue_df.groupby(["year", "month"])["revenue"].sum()).reset_index()\
.assign(
    project = "Project Revenue"
)
revenue_summary = pd.concat([operational_revenue, other_revenue], axis=0).assign(
        date=lambda x: x['month'].astype(int).astype(str) + '/' + x['year'].astype(int).astype(str)
    ).assign(
        date = lambda x: pd.to_datetime(x['date'], format="%m/%Y") + MonthEnd(0)
    )

project_name_map = {
    "Project Revenue": "From Projects",
    "Doanh thu cho thuê HCM": "From Leasing (HCM)",
    "Thưởng nóng": "From Bonus"
}
revenue_summary["project"] = revenue_summary["project"].replace(project_name_map)

revenue_fig_2 = px.bar(
    revenue_summary,
    x='date',
    y="revenue",
    color="project",
    labels={
        "project": "Revenue Sources",
        "revenue": "Revenue",
        "date": "Date"
    },
    title="Monthly Revenue",
    color_discrete_sequence=["#ee5a37", "#acc572", "#143D60"]
)

revenue_fig_2.update_traces(
    hovertemplate="<b>Revenue:</b> %{y:,.0f}",
    customdata=np.stack([revenue_summary["project"]], axis=-1)
)
revenue_fig_2.update_layout(
    hovermode="x unified",
    xaxis_title=None, 
    yaxis_title=None,
    plot_bgcolor="rgba(0, 0, 0, 0)",
    paper_bgcolor="rgba(0, 0, 0, 0)",
    xaxis=dict(
        tickmode='auto',
        nticks=24
    )
)


# Project specific metrics

# ==================
# DASHBOARD
# ==================

st.set_page_config(
    layout="wide"
)

# Import css
with open("./custom.css") as f:
    css = f.read()
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


st.logo(
    os.path.join('assets', "reti_logo.png"),
    size="large",
    # icon_image=os.path.join("assets","reti_small.png")
)
# st.title("RETI LOGO HERE")
st.header("Dashboard")

# st.dataframe(reti_overall)

metric_5, metric_6, metric_7, metric_8 = st.columns(4)
with metric_5:
    with st.container(key="business-metrics-5"):
        st.metric(
            label="Total revenue",
            value= f"{round(sum(reti_overall.revenue)/UNIT, 2)}M",
            border = True
        )
with metric_6:
    with st.container(key="business-metrics-6"):
        st.metric(
            label="Total Gross Profit",
            value=f"{round(sum(reti_overall.grossProfit) / UNIT, 2)}M",
            border=True
        )   
with metric_7:
    with st.container(key="business-metrics-7"):
        st.metric(
            label="Total Gross Profit Margin",
            value=f'''{
                (round((sum(reti_overall.grossProfit)/UNIT) / (sum(reti_overall.revenue)/UNIT), 2)) * 100
            }%''',
            border=True
        )
with metric_8:
    with st.container(key="business-metrics-8"):
        st.metric(
            label="EBT margin",
            # value=round(
            #     sum(reti_overall.ebtMargin)/sum(reti_overall.revenue), 
            #     2
            # ) * 100,
            value = f"{round(0.107503564, 2)*100}%",
            border=True
        )


metric_1, metric_2, metric_3, metric_4 = st.columns(4)
with metric_1:
    with st.container(key="business-metrics-1"):
        st.metric(
            label="Previous Month Revenue",
            value= f"{round((reti_overall.revenue.tail(1).values[0])/UNIT, 2)}M",
            delta= f"{round((reti_overall.changeRevenue.tail(1).values[0]), 2)}% YoY",
            border = True
        )
with metric_2:
    with st.container(key="business-metrics-2"):
        st.metric(
            label="Previous Month Gross profit",
            value=f"{round((reti_overall.grossProfit.tail(1).values[0]) / UNIT, 2)}M",
            delta= f"{round((reti_overall.changeGrossProfit.tail(1).values[0]), 2)}% YoY",
            border=True
        )   
with metric_3:
    with st.container(key="business-metrics-3"):
        st.metric(
            label="Previous Month Gross Profit Margin",
            value=f"{round(reti_overall.profitMargin.tail(1).values[0], 2) * 100}%",
            delta=f"{round(reti_overall.changeProfitMargin.tail(1).values[0] ,2)* 100}% from last year",
            border=True
        )
with metric_4:
    with st.container(key="business-metrics-4"):
        st.metric(
            label="Previous Month EBT margin",
            value=round(reti_overall.ebtMargin.tail(1).values[0], 2),
            delta=f"{round(reti_overall.changeEbtMargin.tail(1).values[0], 2)} YoY",
            border=True
        )

# Second row
col1, col2 = st.columns([1, 3])
with col1:
    with st.container(key="project-metric-4"):
        st.metric(
            label="Number of Projects",
            value=len(project_df["project"].unique()),
            border=True
        )
    with st.container(key="project-metric-1"):
        st.metric(
            label="Project with the **highest** Gross margin",
            value=project_df.iloc[project_df["grossMargin"].idxmax()]["project"],
            border=True
        )
    with st.container(key="project-metric-2"):
        st.metric(
            label="Project with the **lowest** Gross margin",
            value=project_df.iloc[project_df["grossMargin"].idxmin()]["project"],
            border=True
        )
    with st.container(key="project-metric-3"):
        st.metric(
            label="Lowest COGS/Revenue Project",
            value=project_df.iloc[project_df["cogsOverRev"].idxmin()]["project"],
            border=True
        )

with col2:
    with st.container(key="revenue-summary", border=True):
        st.plotly_chart(revenue_fig_2)

# Third row
with st.container(key="project-specific-row"):
    revenue_left, revenue_right = st.columns([0.7, 0.3])
    with revenue_left:
        with st.container(key="project-rev-barchart", border=True):
            # st.subheader(body="Project Gross profit", divider="orange")
            st.plotly_chart(
                revenue_bar
            )
    with revenue_right:
        with st.container(key="project-rev-piechart", border=True):
            # st.subheader(body="Revenue component", divider="orange")
            st.plotly_chart(
                revenue_pie
            )