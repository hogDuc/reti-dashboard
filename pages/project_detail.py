import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Load data from session state
if "project_df" not in st.session_state:
    st.switch_page("app.py")
else:
    project_df = st.session_state.project_df

with st.sidebar:
    st.title("Dashboard Options")
    st.page_link("app.py", label="Overview")
    st.page_link(os.path.join("pages", "project_detail.py"), label="Project Detail")

    selected_project = st.selectbox(
        label="Select Project to View:",
        options=list(
            project_df["project"].unique()
        )
    )


selected_his = st.session_state.df.loc[lambda x: x["project"] == selected_project]
selected_data = st.session_state.project_df.loc[lambda x: x["project"] == selected_project]

with open("./custom.css") as f:
    css = f.read()
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

st.title(selected_project)

# st.dataframe(selected_his.loc[selected_his['revenue'] > 0])

detail_col1, detail_col2, detail_col3, detail_col4 = st.columns(4)
with detail_col1:
    with st.container(key="detail-1"):
        st.metric(
            "Total revenue",
            value = f"{round(selected_data.revenue.values[0] / st.session_state.UNIT, 2)}M",
            border=True,
            delta=f"In {len(selected_his.loc[selected_his['revenue'] > 0])} active month(s)"
        )
with detail_col2:
    with st.container(key="detail-2"):
        st.metric(
            "Total COGS",
            value = f"{round(selected_data.cogs.values[0] / st.session_state.UNIT, 2)}M",
            border=True,
            delta = f"Amounts to {round(selected_data.cogsOverRev.values[0]*100, 2)}% of Revenue"
        )
with detail_col3:
    with st.container(key="detail-3"):
        st.metric(
            "Total Gross Profit",
            value = f"{round(selected_data.grossProfit.values[0] / st.session_state.UNIT, 2)}M",
            border=True
        )
with detail_col4:
    with st.container(key="detail-4"):
        st.metric(
            "Total Gross Profit Margin",
            value = f"{round(selected_data.grossMargin.values[0] * 100, 2)}%",
            border=True
        )

with st.container(key="project-statistics", border=True):
    
    # Prepare data for bar and line chart

    project_barchart = px.bar(
        selected_his,
        x="date",
        y=["revenue", "cogs"],
        barmode="group",
        labels={"value": "Amount", "variable": "Metric", "date": "Date"},
    )

    # Add grossMargin as a line on secondary y-axis
    project_barchart.add_scatter(
        x=selected_his["date"],
        y=selected_his["grossMargin"] * 100, 
        mode="lines+markers",
        name="Gross Margin (%)",
        yaxis="y2",
        line=dict(color="orange")
    )

    # Update layout for secondary y-axis
    project_barchart.update_traces(
        selector=dict(name="Gross Margin (%)"),
        mode="lines+markers",
        connectgaps=True
    )
    project_barchart.update_layout(
        title="Project Revenue, COGS, and Gross Margin Over Time",
        yaxis=dict(title="Amount"),
        yaxis2=dict(
            title="Gross Margin (%)",
            overlaying="y",
            side="right",
            showgrid=False
        ),
        legend=dict(title="Metrics"),
        plot_bgcolor =  "rgba(0, 0, 0, 0)",
        paper_bgcolor = "rgba(0, 0, 0, 0)"
    )


    st.plotly_chart(project_barchart)