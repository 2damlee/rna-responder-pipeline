import textwrap
from pathlib import Path

import pandas as pd
import pytest

from pipeline.utils.config_loader import load_dataset_config
from pipeline.tasks.gse78220 import (
    build_expression_sample_key,
    validate_join_keys,
)


# ---------------------------------------------------------------------------
# config_loader
# ---------------------------------------------------------------------------


def test_load_known_accession(tmp_path):
    config_file = tmp_path / "datasets.yml"
    config_file.write_text(textwrap.dedent("""
        datasets:
          - accession: GSE78220
            sample_id_column: geo_accession
            response_label_fields:
              - characteristics_ch1.1.anti-pd-1 response
            response_mapping:
              Complete Response: responder
            baseline_values:
              - pre-treatment
    """))
    cfg = load_dataset_config("GSE78220", config_path=config_file)
    assert cfg["accession"] == "GSE78220"
    assert cfg["sample_id_column"] == "geo_accession"


def test_load_unknown_accession_raises(tmp_path):
    config_file = tmp_path / "datasets.yml"
    config_file.write_text(textwrap.dedent("""
        datasets:
          - accession: GSE78220
            sample_id_column: geo_accession
    """))
    with pytest.raises(ValueError, match="Dataset config not found: GSE99999"):
        load_dataset_config("GSE99999", config_path=config_file)


def test_both_datasets_loadable_from_actual_config():
    # Reads the real config/datasets.yml — validates it stays parseable
    cfg_78220 = load_dataset_config("GSE78220")
    cfg_91061 = load_dataset_config("GSE91061")

    assert cfg_78220["accession"] == "GSE78220"
    assert cfg_91061["accession"] == "GSE91061"

    # response_mapping must be explicit (no empty dict)
    assert len(cfg_78220["response_mapping"]) > 0
    assert len(cfg_91061["response_mapping"]) > 0


def test_all_response_mapping_values_are_valid(tmp_path):
    # Enforces that any new dataset added to datasets.yml
    # only uses the two allowed normalized labels
    allowed = {"responder", "non_responder"}
    cfg_78220 = load_dataset_config("GSE78220")
    cfg_91061 = load_dataset_config("GSE91061")

    for cfg in [cfg_78220, cfg_91061]:
        for raw_val, normalized in cfg["response_mapping"].items():
            assert normalized in allowed, (
                f"{cfg['accession']}: '{raw_val}' maps to '{normalized}' "
                f"which is not in {allowed}"
            )


# ---------------------------------------------------------------------------
# build_expression_sample_key
# ---------------------------------------------------------------------------


def test_baseline_timepoint_produces_baseline_suffix():
    key = build_expression_sample_key("Pt1", "baseline")
    assert key == "Pt1.baseline"


def test_on_treatment_produces_ontx_suffix():
    key = build_expression_sample_key("Pt1", "on-treatment")
    assert key == "Pt1.OnTx"


def test_unknown_timepoint_returns_none():
    # Only 'baseline' and 'on-treatment' are valid tokens
    key = build_expression_sample_key("Pt1", "follow-up")
    assert key is None


def test_null_patient_label_returns_none():
    import numpy as np
    key = build_expression_sample_key(np.nan, "baseline")
    assert key is None


def test_null_timepoint_returns_none():
    import numpy as np
    key = build_expression_sample_key("Pt1", np.nan)
    assert key is None


def test_patient_label_whitespace_is_stripped():
    key = build_expression_sample_key("  Pt1  ", "baseline")
    assert key == "Pt1.baseline"


# ---------------------------------------------------------------------------
# validate_join_keys
# ---------------------------------------------------------------------------


def _make_parsed_meta(keys: list) -> pd.DataFrame:
    return pd.DataFrame({
        "sample_id": [f"GSM{i:03d}" for i in range(len(keys))],
        "expression_sample_key": keys,
    })


def _make_expr_long(keys: list) -> pd.DataFrame:
    return pd.DataFrame({
        "expression_sample_key": keys,
        "gene_id": ["GENE1"] * len(keys),
        "expression": [1.0] * len(keys),
    })


def test_all_keys_match_returns_summary():
    keys = ["Pt1.baseline", "Pt2.baseline", "Pt3.baseline"]
    parsed_meta = _make_parsed_meta(keys)
    expr_long = _make_expr_long(keys)

    result = validate_join_keys(parsed_meta, expr_long)

    assert result["unmatched_count"] == 0
    assert result["valid_key_count"] == 3
    assert result["none_key_count"] == 0


def test_none_keys_counted_as_warnings_not_errors():
    # Samples where timepoint couldn't be resolved produce None keys.
    # These should be logged as warnings, not raise.
    keys = ["Pt1.baseline", None, "Pt3.baseline"]
    parsed_meta = _make_parsed_meta(keys)
    expr_long = _make_expr_long(["Pt1.baseline", "Pt3.baseline"])

    result = validate_join_keys(parsed_meta, expr_long)

    assert result["none_key_count"] == 1
    assert result["valid_key_count"] == 2
    assert result["unmatched_count"] == 0


def test_unmatched_key_raises_with_informative_message():
    # A valid (non-None) key that doesn't exist in the expression file
    # means the metadata and expression file are misaligned — hard error.
    parsed_meta = _make_parsed_meta(["Pt1.baseline", "Pt99.baseline"])
    expr_long = _make_expr_long(["Pt1.baseline"])  # Pt99 missing

    with pytest.raises(ValueError, match="Join key mismatch"):
        validate_join_keys(parsed_meta, expr_long)


def test_empty_metadata_returns_zero_counts():
    parsed_meta = _make_parsed_meta([])
    expr_long = _make_expr_long(["Pt1.baseline"])

    result = validate_join_keys(parsed_meta, expr_long)

    assert result["none_key_count"] == 0
    assert result["valid_key_count"] == 0
    assert result["unmatched_count"] == 0


def test_all_none_keys_no_raise():
    # All samples lack a resolvable timepoint — warning only
    parsed_meta = _make_parsed_meta([None, None])
    expr_long = _make_expr_long(["Pt1.baseline"])

    result = validate_join_keys(parsed_meta, expr_long)

    assert result["none_key_count"] == 2
    assert result["valid_key_count"] == 0