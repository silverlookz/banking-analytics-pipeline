"""Executive dashboard on the dbt marts.  Run: streamlit run dashboard/app.py"""
import os
from pathlib import Path

import duckdb
import streamlit as st

DB = os.getenv("WAREHOUSE_PATH", str(Path(__file__).resolve().parents[1] / "data" / "warehouse.duckdb"))
st.set_page_config(page_title="Retail Banking KPIs", page_icon="🏦", layout="wide")


@st.cache_data
def q(sql: str):
    with duckdb.connect(DB, read_only=True) as con:
        return con.execute(sql).df()


st.title("🏦 Retail Banking KPIs")
st.caption("Built on dbt marts in DuckDB · synthetic data")

provinces = q("select distinct province from marts.mart_branch_monthly_kpis order by 1")["province"].tolist()
pick = st.multiselect("Province", provinces, default=provinces)
where = "where province in (" + ",".join(f"'{p}'" for p in pick) + ")" if pick else "where 1=0"

kpi = q(f"""select sum(transactions) txns, sum(inflow) inflow, -sum(outflow) outflow,
                   avg(digital_share) digital from marts.mart_branch_monthly_kpis {where}""").iloc[0]
cust = q("select count(*) n, avg(products_held) p, avg(is_dormant::int) d from marts.dim_customers").iloc[0]
c = st.columns(5)
c[0].metric("Customers", f"{cust.n:,.0f}")
c[1].metric("Avg products / customer", f"{cust.p:.2f}")
c[2].metric("Posted transactions", f"{kpi.txns:,.0f}")
c[3].metric("Digital share", f"{kpi.digital:.0%}")
c[4].metric("Dormant customers", f"{cust.d:.0%}")

left, right = st.columns(2)
monthly = q(f"""select transaction_month month, sum(inflow) inflow, -sum(outflow) outflow
                from marts.mart_branch_monthly_kpis {where} group by 1 order by 1""")
left.subheader("Monthly inflow vs outflow")
left.line_chart(monthly.set_index("month"))

branches = q(f"""select branch_name, sum(net_flow) net_flow from marts.mart_branch_monthly_kpis {where}
                 group by 1 order by 2 desc""")
right.subheader("Net flow by branch")
right.bar_chart(branches.set_index("branch_name"))

st.subheader("Spend by category and segment")
spend = q("select category, segment, sum(spend) spend from marts.mart_category_spend_monthly group by 1,2")
st.bar_chart(spend.pivot(index="category", columns="segment", values="spend"))
