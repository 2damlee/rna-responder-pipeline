.PHONY: ingest-78220 ingest-91061 ingest-all dbt-run dbt-test test analysis pipeline clean help

help:
	@echo "Available commands:"
	@echo "  make ingest-78220   Run GSE78220 ingestion pipeline"
	@echo "  make ingest-91061   Run GSE91061 ingestion pipeline (auto-downloads expression file)"
	@echo "  make ingest-all     Run both datasets"
	@echo "  make dbt-run        Build all dbt models"
	@echo "  make dbt-test       Run all dbt tests"
	@echo "  make test           Run unit tests"
	@echo "  make analysis       Run all analysis scripts (requires dbt-run first)"
	@echo "  make pipeline       Full pipeline: ingest → dbt → analysis"
	@echo "  make clean          Remove generated data and logs"

ingest-78220:
	python -m pipeline.flows.ingest_geo --accession GSE78220

ingest-91061:
	python -m pipeline.flows.ingest_geo --accession GSE91061

ingest-all: ingest-78220 ingest-91061

dbt-run:
	dbt run --project-dir dbt

dbt-test:
	dbt test --project-dir dbt

test:
	python -m pytest -v

analysis:
	python analysis/scripts/pca.py
	python analysis/scripts/heatmap.py
	python analysis/scripts/boxplot.py
	python analysis/scripts/group_comparison.py

pipeline: ingest-all dbt-run dbt-test analysis

clean:
	rm -rf data/processed/
	rm -rf data/curated/
	rm -rf outputs/logs/
	@echo "Cleaned processed data and logs. Raw data preserved."