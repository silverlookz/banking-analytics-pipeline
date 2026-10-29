.PHONY: all ingest build rebuild docs dashboard test clean

all: ingest rebuild

ingest:
	python ingest/extract_load.py

build:
	cd transform && dbt build --profiles-dir .

rebuild:
	cd transform && dbt build --profiles-dir . --full-refresh

docs:
	cd transform && dbt docs generate --profiles-dir . && dbt docs serve --profiles-dir .

dashboard:
	streamlit run dashboard/app.py

test:
	pytest -q

clean:
	rm -rf data/warehouse.duckdb data/raw transform/target transform/logs
