from __future__ import annotations

import argparse
import os

from prefect import flow, task


@task(name="build_baseline_dataset", log_prints=True)
def task_build_baseline_dataset(accession: str):
    if accession == "GSE78220":
        from pipeline.tasks.gse78220 import build_baseline_dataset
    elif accession == "GSE91061":
        from pipeline.tasks.gse91061 import build_baseline_dataset
    else:
        raise ValueError(f"Unknown accession: {accession}")
    return build_baseline_dataset()


@task(name="save_baseline_outputs", log_prints=True)
def task_save_baseline_outputs(
    parsed_meta, expr_long, baseline, qc_summary, accession: str
):
    if accession == "GSE78220":
        from pipeline.tasks.gse78220 import save_baseline_outputs
    elif accession == "GSE91061":
        from pipeline.tasks.gse91061 import save_baseline_outputs
    else:
        raise ValueError(f"Unknown accession: {accession}")

    save_baseline_outputs(parsed_meta, expr_long, baseline, qc_summary)

    summary = {
        "accession": accession,
        "parsed_metadata_rows": len(parsed_meta),
        "baseline_rows": len(baseline),
        "baseline_samples": int(baseline["sample_id"].nunique()),
        "baseline_genes": int(baseline["gene_id"].nunique()),
    }
    print("Saved outputs summary:", summary)
    return summary


@task(name="log_pipeline_run", log_prints=True)
def task_log_pipeline_run(accession: str, summary: dict):
    from pipeline.tasks.log_run import log_pipeline_run
    location = log_pipeline_run(accession, summary)
    print(f"Run log location: {location}")
    return location


@task(name="upload_to_s3", log_prints=True)
def task_upload_to_s3(accession: str):
    if not os.getenv("S3_BUCKET_NAME"):
        print("S3_BUCKET_NAME not set — skipping S3 upload")
        return None

    from pipeline.tasks.s3_upload import upload_processed_outputs
    results = upload_processed_outputs(accession.lower())
    print("S3 upload complete:", results)
    return results


@flow(name="geo_rna_ingestion", log_prints=True)
def geo_rna_ingestion_flow(
    accession: str = "GSE78220",
    upload_s3: bool = False,
):
    parsed_meta, expr_long, baseline, qc_summary = task_build_baseline_dataset(
        accession
    )
    summary = task_save_baseline_outputs(
        parsed_meta, expr_long, baseline, qc_summary, accession
    )
    task_log_pipeline_run(accession, summary)

    if upload_s3:
        task_upload_to_s3(accession)

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run GEO RNA ingestion pipeline")
    parser.add_argument(
        "--accession",
        default="GSE78220",
        choices=["GSE78220", "GSE91061"],
        help="GEO accession to process (default: GSE78220)",
    )
    parser.add_argument(
        "--upload-s3",
        action="store_true",
        help="Upload processed parquets to S3 after saving locally.",
    )
    args = parser.parse_args()
    geo_rna_ingestion_flow(accession=args.accession, upload_s3=args.upload_s3)