"""Extract + Load: generate raw retail-banking source files and land them in DuckDB.

The raw data deliberately contains the problems real source systems have:
duplicate customer rows, mixed-case codes, untrimmed strings, missing emails,
amounts stored in cents, reversed transactions and late-arriving records.
Cleaning them is the job of the dbt staging layer.

    python ingest/extract_load.py   ->  data/raw/*.csv + data/warehouse.duckdb (schema raw)
"""
from __future__ import annotations

import csv
import os
import random
from datetime import date, datetime, timedelta
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = Path(os.getenv("RAW_DIR", ROOT / "data" / "raw"))
DB = Path(os.getenv("WAREHOUSE_PATH", ROOT / "data" / "warehouse.duckdb"))

BRANCHES = [("BR01", "Toronto Downtown", "ON"), ("BR02", "Mississauga", "ON"), ("BR03", "Ottawa", "ON"),
            ("BR04", "Montreal Centre", "QC"), ("BR05", "Vancouver West", "BC"), ("BR06", "Calgary", "AB"),
            ("BR07", "Halifax", "NS"), ("BR08", "Oshawa", "ON")]
FIRST = ["Aisha", "Ben", "Chen", "Diego", "Elena", "Farah", "Gabe", "Hana", "Ivan", "Jia", "Kofi", "Lena",
         "Marco", "Nadia", "Omar", "Priya", "Quinn", "Rosa", "Sam", "Tara", "Uma", "Victor", "Wen", "Yusuf"]
LAST = ["Ahmed", "Brown", "Chen", "Dubois", "Evans", "Fernandes", "Gill", "Huang", "Ito", "Johnson",
        "Khan", "Lee", "Martin", "Nguyen", "Okafor", "Patel", "Roy", "Singh", "Tremblay", "Wong"]
PRODUCTS = ["chequing", "savings", "credit_card", "line_of_credit"]
CATEGORIES = ["groceries", "dining", "travel", "utilities", "transfer", "payroll", "retail", "fees"]
CHANNELS = ["mobile", "online", "branch", "atm", "pos"]


def write_csv(path: Path, header: list[str], rows: list[tuple]) -> None:
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def generate(seed: int = 7, n_customers: int = 800, n_txn: int = 40000) -> None:
    rng = random.Random(seed)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    write_csv(RAW_DIR / "branches.csv", ["branch_code", "branch_name", "province"],
              [(c, f"  {n} ", p) for c, n, p in BRANCHES])  # untrimmed names

    customers = []
    for cid in range(1, n_customers + 1):
        fn, ln = rng.choice(FIRST), rng.choice(LAST)
        email = "" if rng.random() < 0.04 else f"{fn}.{ln}{cid}@example.com".lower()
        opened = date(2019, 1, 1) + timedelta(days=rng.randint(0, 2000))
        seg = rng.choices(["mass", "affluent", "private", "small_business"], [0.62, 0.25, 0.05, 0.08])[0]
        updated = datetime(2025, 1, 1) + timedelta(hours=rng.randint(0, 8000))
        row = (cid, fn, ln, email, rng.choice(["", "1980", "1975", "1992", "2001", "1968"]),
               seg.upper() if rng.random() < 0.2 else seg, rng.choice(BRANCHES)[0], opened.isoformat(),
               updated.isoformat(sep=" "))
        customers.append(row)
        if rng.random() < 0.03:  # duplicate from a CRM re-sync with a later timestamp
            customers.append(row[:-1] + ((updated + timedelta(days=3)).isoformat(sep=" "),))
    write_csv(RAW_DIR / "customers.csv", ["customer_id", "first_name", "last_name", "email", "birth_year",
                                          "segment", "home_branch", "opened_on", "_updated_at"], customers)

    accounts, aid = [], 1000
    for c in customers:
        if any(a[1] == c[0] for a in accounts):
            continue
        for product in rng.sample(PRODUCTS, k=rng.choices([1, 2, 3], [0.4, 0.4, 0.2])[0]):
            aid += 1
            limit = rng.choice([2000, 5000, 10000, 25000]) * 100 if product in ("credit_card", "line_of_credit") else 0
            accounts.append((aid, c[0], product, c[7], "" if rng.random() > 0.05 else "2025-06-30", limit))
    write_csv(RAW_DIR / "accounts.csv", ["account_id", "customer_id", "product_type", "opened_on", "closed_on",
                                         "credit_limit_cents"], accounts)

    txns = []
    start = datetime(2024, 1, 1)
    for tid in range(1, n_txn + 1):
        acct = rng.choice(accounts)
        cat = rng.choices(CATEGORIES, [0.22, 0.14, 0.05, 0.1, 0.15, 0.08, 0.22, 0.04])[0]
        sign = 1 if cat == "payroll" else -1
        base = {"groceries": 90, "dining": 45, "travel": 600, "utilities": 140, "transfer": 400,
                "payroll": 2600, "retail": 120, "fees": 12}[cat]
        amount_cents = sign * int(rng.lognormvariate(0, 0.6) * base * 100)
        ts = start + timedelta(minutes=int(rng.random() ** 0.9 * 730 * 24 * 60))
        status = rng.choices(["posted", "posted", "posted", "pending", "reversed"], [0.5, 0.3, 0.12, 0.05, 0.03])[0]
        progress = (ts - start).days / 730  # digital adoption grows over the two years
        digital = 0.32 + 0.25 * progress
        channel = rng.choices(CHANNELS, [digital * 0.65, digital * 0.35, (1 - digital) * 0.25,
                                         (1 - digital) * 0.25, (1 - digital) * 0.5])[0]
        txns.append((tid, acct[0], ts.isoformat(sep=" "), amount_cents, cat.title() if rng.random() < 0.1 else cat,
                     channel, status, (ts + timedelta(days=rng.choice([0, 0, 0, 1, 2, 9]))).isoformat(sep=" ")))
    write_csv(RAW_DIR / "transactions.csv", ["transaction_id", "account_id", "transaction_ts", "amount_cents",
                                             "category", "channel", "status", "_loaded_at"], txns)


def load() -> None:
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB))
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    for name in ("branches", "customers", "accounts", "transactions"):
        con.execute(f"CREATE OR REPLACE TABLE raw.{name} AS "
                    f"SELECT * FROM read_csv_auto('{RAW_DIR / (name + '.csv')}', all_varchar=true)")
        print(f"raw.{name}: {con.execute(f'SELECT COUNT(*) FROM raw.{name}').fetchone()[0]:,} rows")
    con.close()


if __name__ == "__main__":
    generate()
    load()
