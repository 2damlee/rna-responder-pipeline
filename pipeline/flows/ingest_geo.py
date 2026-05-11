from __future__ import annotations

import argparse
import os

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


@task(name="upload_to_s3", log_prints=True)
def task_upload_to_s3(accession: str = "gse78220"):
    if not os.getenv("S3_BUCKET_NAME"):
        print("S3_BUCKET_NAME not set — skipping S3 upload")
        return None

    from pipeline.tasks.s3_upload import upload_processed_outputs

    results = upload_processed_outputs(accession)
    print("S3 upload complete:", results)
    return results


@flow(name="geo_rna_ingestion", log_prints=True)
def geo_rna_ingestion_flow(upload_s3: bool = False):
    parsed_meta, expr_long, baseline, qc_summary = task_build_baseline_dataset()
    summary = task_save_baseline_outputs(parsed_meta, expr_long, baseline, qc_summary)

    if upload_s3:
        task_upload_to_s3()

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run GEO RNA ingestion pipeline")
    parser.add_argument(
        "--upload-s3",
        action="store_true",
        help="Upload processed parquets to S3 after saving locally. "
             "Requires S3_BUCKET_NAME to be set in environment.",
    )
    args = parser.parse_args()
    geo_rna_ingestion_flow(upload_s3=args.upload_s3)