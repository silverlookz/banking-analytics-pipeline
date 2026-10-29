"""Render a static PNG summary of the marts (used in the README)."""
import os
import sys
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB = os.getenv("WAREHOUSE_PATH", str(ROOT / "data" / "warehouse.duckdb"))
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs" / "dashboard.png"
money = FuncFormatter(lambda v, _: f"${v / 1e6:.1f}M" if abs(v) >= 1e6 else f"${v / 1e3:.0f}K")

with duckdb.connect(DB, read_only=True) as con:
    monthly = con.execute("""select transaction_month m, sum(inflow) i, -sum(outflow) o
                             from marts.mart_branch_monthly_kpis group by 1 order by 1""").df()
    branch = con.execute("""select branch_name b, sum(net_flow) n from marts.mart_branch_monthly_kpis
                            group by 1 order by 2""").df()
    digital = con.execute("""select transaction_month m, avg(digital_share) d
                             from marts.mart_branch_monthly_kpis group by 1 order by 1""").df()
    cat = con.execute("""select category c, sum(spend) s from marts.mart_category_spend_monthly
                         group by 1 order by 2""").df()

fig, ax = plt.subplots(2, 2, figsize=(13, 8))
ax[0, 0].plot(monthly.m, monthly.i, label="Inflow", color="#16a34a")
ax[0, 0].plot(monthly.m, monthly.o, label="Outflow", color="#dc2626")
ax[0, 0].yaxis.set_major_formatter(money); ax[0, 0].legend(frameon=False)
ax[0, 0].set_title("Monthly inflow vs outflow", loc="left")
ax[0, 1].barh(branch.b, branch.n, color=["#dc2626" if v < 0 else "#2563eb" for v in branch.n])
ax[0, 1].xaxis.set_major_formatter(money); ax[0, 1].set_title("Net flow by branch", loc="left")
ax[1, 0].plot(digital.m, digital.d * 100, color="#7c3aed")
ax[1, 0].set_title("Digital channel share (%)", loc="left")
ax[1, 1].barh(cat.c, cat.s, color="#2563eb"); ax[1, 1].xaxis.set_major_formatter(money)
ax[1, 1].set_title("Spend by category", loc="left")
for a in ax.flat:
    a.spines[["top", "right"]].set_visible(False); a.grid(alpha=0.25)
fig.suptitle("Retail Banking KPIs (synthetic data)", x=0.01, ha="left", fontsize=14)
fig.tight_layout()
fig.savefig(OUT, dpi=110)
print(f"wrote {OUT}")
