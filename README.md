# RNA Responder Pipeline

End-to-end transcriptomics data pipeline for comparing immunotherapy responder vs non-responder cohorts using public GEO RNA-seq data.

## Current scope

This repository starts with a single-study MVP based on GSE78220.

Current focus:
- inspect raw GEO metadata
- define reliable parsing rules for response and timepoint
- build reproducible processed outputs
- prepare DuckDB/dbt-friendly parquet datasets

## Planned stack

- Python 3.11
- pandas
- GEOparse
- Prefect 2.x
- pyarrow
- DuckDB
- dbt-core
- dbt-duckdb
- scikit-learn
- matplotlib

## Project stages

1. MVP
   - inspect GSE78220 metadata
   - define parser rules
   - generate baseline long-format parquet
   - build minimal DuckDB/dbt models
   - create PCA / heatmap / boxplot outputs

2. Stabilization
   - organize Prefect flows
   - document architecture
   - separate config and environment settings
   - make local reruns reliable

3. Expansion
   - add GSE91061
   - extend dataset registry
   - unify multi-study schema
   - optionally migrate to Athena/S3

## Repository status

Initial repository setup with metadata inspection workflow for GSE78220.