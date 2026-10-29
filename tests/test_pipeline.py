"""End-to-end: extract/load into a temp warehouse, run dbt build, check the marts."""
import os
import subprocess
import sys
from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def warehouse(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("wh")
    env = {**os.environ, "WAREHOUSE_PATH": str(tmp / "wh.duckdb"), "RAW_DIR": str(tmp / "raw")}
    subprocess.run([sys.executable, "ingest/extract_load.py"], cwd=ROOT, env=env, check=True)
    build = subprocess.run(["dbt", "build", "--profiles-dir", "."], cwd=ROOT / "transform", env=env,
                           capture_output=True, text=True)
    assert build.returncode == 0, build.stdout[-3000:]
    return env["WAREHOUSE_PATH"]


def test_duplicates_removed(warehouse):
    with duckdb.connect(warehouse, read_only=True) as con:
        raw = con.execute("select count(*), count(distinct customer_id) from raw.customers").fetchone()
        dim = con.execute("select count(*) from marts.dim_customers").fetchone()[0]
    assert raw[0] > raw[1] and dim == raw[1]


def test_only_posted_transactions(warehouse):
    with duckdb.connect(warehouse, read_only=True) as con:
        posted = con.execute("select count(*) from raw.transactions where lower(trim(status))='posted'").fetchone()[0]
        fact = con.execute("select count(*) from marts.fct_transactions").fetchone()[0]
    assert posted == fact


def test_branch_kpis(warehouse):
    with duckdb.connect(warehouse, read_only=True) as con:
        branches, months = con.execute(
            "select count(distinct branch_code), count(distinct transaction_month) from marts.mart_branch_monthly_kpis"
        ).fetchone()
    assert branches == 8 and months == 24
