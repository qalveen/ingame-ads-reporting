MONTH ?= 2026-09
PY ?= python3

.PHONY: setup data report test docs all clean

setup:
	$(PY) -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

data:            ## regenerate synthetic raw feeds
	$(PY) src/generate_data.py

report:          ## build models, run tests, publish report for MONTH
	$(PY) src/run_pipeline.py --month $(MONTH)

docs:            ## re-render KPI docs from YAML
	$(PY) src/render_docs.py

all: data docs
	$(PY) src/run_pipeline.py --month 2026-08
	$(PY) src/run_pipeline.py --month 2026-09

clean:
	rm -rf data/raw data/*.duckdb output/*
