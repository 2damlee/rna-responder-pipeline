from __future__ import annotations

from prefect import flow, task

from pipeline.tasks.gse78220 import (
    build_baseline_dataset,
    save_baseline_outputs,
)


@task(name="build_baseline_dataset", log_prints=True)
def task_build_baseline_dataset():
    return build_baseline_dataset()


@task(name="save_baseline_outputs", log_prints=True)
def task_save_baseline_outputs(parsed_meta, expr_long, baseline, qc_summary):
    save_baseline_outputs(parsed_meta, expr_long, baseline, qc_summary)

    summary = {
        "parsed_metadata_rows": len(parsed_meta),
        "expression_long_rows": len(expr_long),
        "baseline_rows": len(baseline),
        "baseline_samples": baseline["sample_id"].nunique(),
        "baseline_genes": baseline["gene_id"].nunique(),
    }

    print("Saved outputs summary:", summary)
    return summary


@flow(name="geo_rna_ingestion", log_prints=True)
def geo_rna_ingestion_flow():
    parsed_meta, expr_long, baseline, qc_summary = task_build_baseline_dataset()
    return task_save_baseline_outputs(parsed_meta, expr_long, baseline, qc_summary)


if __name__ == "__main__":
    geo_rna_ingestion_flow()