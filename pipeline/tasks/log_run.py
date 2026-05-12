"""
Pipeline run logging to S3.

After each successful pipeline run, writes a JSON log entry to:
  s3://<bucket>/logs/pipeline_runs/<accession>/<timestamp>.json

This provides a lightweight audit trail without external monitoring tooling.
If S3_BUCKET_NAME is not set, logs to local outputs/logs/ instead.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _build_record(accession: str, summary: dict) -> dict:
    return {
        "accession": accession,
        "timestamp": _timestamp(),
        "summary": summary,
    }


def log_run_local(accession: str, summary: dict) -> str:
    """Fallback: write run log to local outputs/logs/."""
    log_dir = Path("outputs/logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    ts = _timestamp()
    path = log_dir / f"{accession}_{ts}.json"
    record = _build_record(accession, summary)

    path.write_text(json.dumps(record, indent=2))
    print(f"Run log saved locally: {path}")
    return str(path)


def log_run_s3(accession: str, summary: dict) -> str:
    """Write run log to S3 under logs/pipeline_runs/<accession>/."""
    import boto3

    bucket = os.getenv("S3_BUCKET_NAME")
    if not bucket:
        raise EnvironmentError("S3_BUCKET_NAME not set")

    ts = _timestamp()
    key = f"logs/pipeline_runs/{accession}/{ts}.json"
    record = _build_record(accession, summary)

    boto3.client("s3").put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(record, indent=2),
        ContentType="application/json",
    )

    s3_uri = f"s3://{bucket}/{key}"
    print(f"Run log saved to S3: {s3_uri}")
    return s3_uri


def log_pipeline_run(accession: str, summary: dict) -> str:
    """
    Log pipeline run results.
    Uses S3 if S3_BUCKET_NAME is set, otherwise falls back to local file.
    """
    if os.getenv("S3_BUCKET_NAME"):
        return log_run_s3(accession, summary)
    return log_run_local(accession, summary)