from __future__ import annotations

import os
from pathlib import Path

import boto3
from botocore.exceptions import ClientError


def get_s3_client():
    return boto3.client(
        "s3",
        region_name=os.getenv("AWS_DEFAULT_REGION", "eu-central-1"),
    )


def upload_file_to_s3(local_path: Path, s3_key: str) -> str:
    """
    Upload a single local file to S3.
    Returns the full s3:// URI of the uploaded object.
    Raises EnvironmentError if S3_BUCKET_NAME is not set.
    Raises FileNotFoundError if the local file does not exist.
    """
    bucket = os.getenv("S3_BUCKET_NAME")
    if not bucket:
        raise EnvironmentError(
            "S3_BUCKET_NAME environment variable is not set. "
            "Add it to your .env file."
        )

    if not local_path.exists():
        raise FileNotFoundError(f"Local file not found: {local_path}")

    s3 = get_s3_client()
    try:
        s3.upload_file(str(local_path), bucket, s3_key)
    except ClientError as e:
        raise RuntimeError(
            f"S3 upload failed for {local_path}: {e}"
        ) from e

    s3_uri = f"s3://{bucket}/{s3_key}"
    print(f"Uploaded: {local_path} → {s3_uri}")
    return s3_uri


def upload_processed_outputs(accession: str = "gse78220") -> dict[str, str]:
    files_to_upload: dict[Path, str] = {
        Path(f"data/processed/{accession}/baseline_long.parquet"): (
            f"processed/{accession}/baseline/baseline_long.parquet"
        ),
        Path(f"data/processed/{accession}/parsed_metadata.parquet"): (
            f"processed/{accession}/metadata/parsed_metadata.parquet"
        ),
        Path(f"data/processed/{accession}/expression_long.parquet"): (
            f"processed/{accession}/full/expression_long.parquet"
        ),
    }

    results: dict[str, str] = {}
    for local_path, s3_key in files_to_upload.items():
        s3_uri = upload_file_to_s3(local_path, s3_key)
        results[str(local_path)] = s3_uri

    return results