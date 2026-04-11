from __future__ import annotations

from typing import Any
import pandas as pd


def _normalize_text(value: Any) -> str | None:
    if pd.isna(value):
        return None

    text = str(value).strip()
    if text == "":
        return None

    return text


def _extract_first_available(row: pd.Series, fields: list[str]) -> str | None:
    for field in fields:
        if field not in row.index:
            continue

        value = _normalize_text(row[field])
        if value is not None:
            return value

    return None


def parse_metadata(meta_df: pd.DataFrame, dataset_cfg: dict[str, Any]) -> pd.DataFrame:
    sample_id_column = dataset_cfg["sample_id_column"]
    response_fields = dataset_cfg.get("response_label_fields", [])
    timepoint_fields = dataset_cfg.get("timepoint_fields", [])
    response_mapping = dataset_cfg.get("response_mapping", {})
    baseline_values = set(dataset_cfg.get("baseline_values", []))
    dataset_accession = dataset_cfg["accession"]

    if sample_id_column not in meta_df.columns:
        raise KeyError(f"Missing sample_id_column: {sample_id_column}")

    parsed = meta_df.copy()

    parsed["sample_id"] = parsed[sample_id_column].astype(str).str.strip()

    parsed["response_raw"] = parsed.apply(
        lambda row: _extract_first_available(row, response_fields),
        axis=1,
    )

    parsed["timepoint_raw"] = parsed.apply(
        lambda row: _extract_first_available(row, timepoint_fields),
        axis=1,
    )

    parsed["response_label"] = parsed["response_raw"].map(response_mapping)

    parsed["timepoint"] = parsed["timepoint_raw"].apply(
        lambda x: "baseline" if x in baseline_values else x
    )

    parsed["dataset_accession"] = dataset_accession

    return parsed[
        [
            "sample_id",
            "response_raw",
            "response_label",
            "timepoint_raw",
            "timepoint",
            "dataset_accession",
        ]
    ].copy()