import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pipeline.tasks.log_run import log_pipeline_run, log_run_local, _build_record
from pipeline.tasks.s3_upload import upload_file_to_s3, upload_processed_outputs


# ---------------------------------------------------------------------------
# _build_record
# ---------------------------------------------------------------------------


def test_build_record_contains_required_fields():
    record = _build_record("GSE78220", {"baseline_rows": 682236})
    assert record["accession"] == "GSE78220"
    assert "timestamp" in record
    assert record["summary"]["baseline_rows"] == 682236


def test_build_record_timestamp_format():
    record = _build_record("GSE78220", {})
    ts = record["timestamp"]
    # Format: 20260512T073446Z
    assert len(ts) == 16
    assert ts.endswith("Z")
    assert "T" in ts


# ---------------------------------------------------------------------------
# log_run_local
# ---------------------------------------------------------------------------


def test_log_run_local_creates_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    location = log_run_local("GSE78220", {"baseline_rows": 682236})
    log_path = Path(location)

    assert log_path.exists()
    content = json.loads(log_path.read_text())
    assert content["accession"] == "GSE78220"
    assert content["summary"]["baseline_rows"] == 682236


def test_log_run_local_creates_outputs_logs_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    log_run_local("GSE91061", {})
    assert (tmp_path / "outputs" / "logs").is_dir()


def test_log_run_local_filename_contains_accession_and_timestamp(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    location = log_run_local("GSE78220", {})
    filename = Path(location).name
    assert filename.startswith("GSE78220_")
    assert filename.endswith(".json")


# ---------------------------------------------------------------------------
# log_pipeline_run — routing logic
# ---------------------------------------------------------------------------


def test_log_pipeline_run_uses_local_when_s3_not_set(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("S3_BUCKET_NAME", raising=False)

    location = log_pipeline_run("GSE78220", {"baseline_rows": 100})
    assert "outputs/logs" in location


def test_log_pipeline_run_uses_s3_when_bucket_set(tmp_path, monkeypatch):
    monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket")

    with patch("boto3.client") as mock_client_constructor:
        mock_client = MagicMock()
        mock_client_constructor.return_value = mock_client

        location = log_pipeline_run("GSE78220", {"baseline_rows": 100})

    assert location.startswith("s3://test-bucket/logs/pipeline_runs/GSE78220/")
    mock_client.put_object.assert_called_once()

    call_kwargs = mock_client.put_object.call_args.kwargs
    assert call_kwargs["Bucket"] == "test-bucket"
    assert call_kwargs["ContentType"] == "application/json"

    body = json.loads(call_kwargs["Body"])
    assert body["accession"] == "GSE78220"


# ---------------------------------------------------------------------------
# upload_file_to_s3
# ---------------------------------------------------------------------------


def test_upload_raises_when_bucket_not_set(tmp_path, monkeypatch):
    monkeypatch.delenv("S3_BUCKET_NAME", raising=False)
    fake_file = tmp_path / "test.parquet"
    fake_file.write_bytes(b"data")

    with pytest.raises(EnvironmentError, match="S3_BUCKET_NAME"):
        upload_file_to_s3(fake_file, "processed/gse78220/baseline/test.parquet")


def test_upload_raises_when_local_file_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket")
    missing = tmp_path / "does_not_exist.parquet"

    with pytest.raises(FileNotFoundError):
        upload_file_to_s3(missing, "processed/gse78220/baseline/test.parquet")


def test_upload_calls_boto3_with_correct_args(tmp_path, monkeypatch):
    monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "eu-central-1")

    fake_file = tmp_path / "baseline_long.parquet"
    fake_file.write_bytes(b"parquet data")

    with patch("pipeline.tasks.s3_upload.boto3") as mock_boto3:
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        uri = upload_file_to_s3(
            fake_file,
            "processed/gse78220/baseline/baseline_long.parquet",
        )

    mock_client.upload_file.assert_called_once_with(
        str(fake_file),
        "test-bucket",
        "processed/gse78220/baseline/baseline_long.parquet",
    )
    assert uri == "s3://test-bucket/processed/gse78220/baseline/baseline_long.parquet"


# ---------------------------------------------------------------------------
# upload_processed_outputs — S3 key structure
# ---------------------------------------------------------------------------


def test_upload_processed_outputs_uses_correct_s3_key_structure(tmp_path, monkeypatch):
    monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket")

    # Create fake local files
    proc_dir = tmp_path / "data" / "processed" / "gse78220"
    proc_dir.mkdir(parents=True)
    (proc_dir / "baseline_long.parquet").write_bytes(b"data")
    (proc_dir / "parsed_metadata.parquet").write_bytes(b"data")
    (proc_dir / "expression_long.parquet").write_bytes(b"data")

    monkeypatch.chdir(tmp_path)

    uploaded_keys = []

    with patch("pipeline.tasks.s3_upload.boto3") as mock_boto3:
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        def capture_upload(local, bucket, key):
            uploaded_keys.append(key)

        mock_client.upload_file.side_effect = capture_upload

        upload_processed_outputs("gse78220")

    # baseline goes to baseline/, others to separate subdirs
    assert any("baseline/baseline_long.parquet" in k for k in uploaded_keys)
    assert any("metadata/parsed_metadata.parquet" in k for k in uploaded_keys)
    assert any("full/expression_long.parquet" in k for k in uploaded_keys)

    # no file should be at the folder root (prevents Athena reading wrong files)
    for key in uploaded_keys:
        parts = key.split("/")
        assert len(parts) >= 4, f"Key '{key}' is too shallow — Athena may scan wrong files"