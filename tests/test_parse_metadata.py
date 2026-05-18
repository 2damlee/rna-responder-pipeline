import numpy as np
import pandas as pd
import pytest

from pipeline.tasks.parse_metadata import parse_metadata


# Minimal config that mirrors what datasets.yml provides for GSE78220
GSE78220_CFG = {
    "accession": "GSE78220",
    "sample_id_column": "geo_accession",
    "response_label_fields": ["characteristics_ch1.1.anti-pd-1 response"],
    "timepoint_fields": [
        "characteristics_ch1.12.biopsy time",
        "characteristics_ch1.13.biopsy time",
    ],
    "response_mapping": {
        "Complete Response": "responder",
        "Partial Response": "responder",
        "Progressive Disease": "non_responder",
    },
    "baseline_values": ["pre-treatment"],
}

# Minimal config for GSE91061
GSE91061_CFG = {
    "accession": "GSE91061",
    "sample_id_column": "title",
    "response_label_fields": ["characteristics_ch1.1.response"],
    "timepoint_fields": ["characteristics_ch1.0.visit (pre or on treatment)"],
    "response_mapping": {
        "PD": "non_responder",
    },
    "baseline_values": ["Pre"],
}


def make_meta(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# response_label mapping
# ---------------------------------------------------------------------------


def test_complete_response_maps_to_responder():
    meta = make_meta([{
        "geo_accession": "GSM001",
        "characteristics_ch1.1.anti-pd-1 response": "Complete Response",
        "characteristics_ch1.12.biopsy time": "pre-treatment",
    }])
    result = parse_metadata(meta, GSE78220_CFG)
    assert result.loc[0, "response_label"] == "responder"


def test_partial_response_maps_to_responder():
    meta = make_meta([{
        "geo_accession": "GSM002",
        "characteristics_ch1.1.anti-pd-1 response": "Partial Response",
        "characteristics_ch1.12.biopsy time": "pre-treatment",
    }])
    result = parse_metadata(meta, GSE78220_CFG)
    assert result.loc[0, "response_label"] == "responder"


def test_progressive_disease_maps_to_non_responder():
    meta = make_meta([{
        "geo_accession": "GSM003",
        "characteristics_ch1.1.anti-pd-1 response": "Progressive Disease",
        "characteristics_ch1.12.biopsy time": "pre-treatment",
    }])
    result = parse_metadata(meta, GSE78220_CFG)
    assert result.loc[0, "response_label"] == "non_responder"


def test_unknown_response_value_becomes_null():
    # "Stable Disease" is not in the mapping — should be NaN, not raise
    meta = make_meta([{
        "geo_accession": "GSM004",
        "characteristics_ch1.1.anti-pd-1 response": "Stable Disease",
        "characteristics_ch1.12.biopsy time": "pre-treatment",
    }])
    result = parse_metadata(meta, GSE78220_CFG)
    assert pd.isna(result.loc[0, "response_label"])


def test_missing_response_field_becomes_null():
    meta = make_meta([{
        "geo_accession": "GSM005",
        "characteristics_ch1.12.biopsy time": "pre-treatment",
        # response field missing entirely
    }])
    result = parse_metadata(meta, GSE78220_CFG)
    assert pd.isna(result.loc[0, "response_raw"])
    assert pd.isna(result.loc[0, "response_label"])


# ---------------------------------------------------------------------------
# timepoint normalization
# ---------------------------------------------------------------------------


def test_pre_treatment_becomes_baseline():
    meta = make_meta([{
        "geo_accession": "GSM006",
        "characteristics_ch1.1.anti-pd-1 response": "Complete Response",
        "characteristics_ch1.12.biopsy time": "pre-treatment",
    }])
    result = parse_metadata(meta, GSE78220_CFG)
    assert result.loc[0, "timepoint"] == "baseline"
    assert result.loc[0, "timepoint_raw"] == "pre-treatment"


def test_non_baseline_timepoint_passes_through():
    meta = make_meta([{
        "geo_accession": "GSM007",
        "characteristics_ch1.1.anti-pd-1 response": "Complete Response",
        "characteristics_ch1.12.biopsy time": "on-treatment",
    }])
    result = parse_metadata(meta, GSE78220_CFG)
    assert result.loc[0, "timepoint"] == "on-treatment"


def test_missing_timepoint_field_becomes_null():
    meta = make_meta([{
        "geo_accession": "GSM008",
        "characteristics_ch1.1.anti-pd-1 response": "Complete Response",
        # no timepoint field
    }])
    result = parse_metadata(meta, GSE78220_CFG)
    assert pd.isna(result.loc[0, "timepoint_raw"])


# ---------------------------------------------------------------------------
# timepoint field fallback (GSE78220 has 3 candidate fields)
# ---------------------------------------------------------------------------


def test_primary_timepoint_field_takes_priority():
    meta = make_meta([{
        "geo_accession": "GSM009",
        "characteristics_ch1.1.anti-pd-1 response": "Complete Response",
        "characteristics_ch1.12.biopsy time": "pre-treatment",
        "characteristics_ch1.13.biopsy time": "on-treatment",  # secondary field
    }])
    result = parse_metadata(meta, GSE78220_CFG)
    # primary field should win
    assert result.loc[0, "timepoint_raw"] == "pre-treatment"
    assert result.loc[0, "timepoint"] == "baseline"


def test_falls_back_to_secondary_timepoint_field():
    meta = make_meta([{
        "geo_accession": "GSM010",
        "characteristics_ch1.1.anti-pd-1 response": "Complete Response",
        # primary field absent, secondary field present
        "characteristics_ch1.13.biopsy time": "pre-treatment",
    }])
    result = parse_metadata(meta, GSE78220_CFG)
    assert result.loc[0, "timepoint_raw"] == "pre-treatment"
    assert result.loc[0, "timepoint"] == "baseline"


# ---------------------------------------------------------------------------
# sample_id extraction
# ---------------------------------------------------------------------------


def test_sample_id_is_extracted_from_configured_column():
    meta = make_meta([{
        "geo_accession": "GSM999",
        "characteristics_ch1.1.anti-pd-1 response": "Complete Response",
        "characteristics_ch1.12.biopsy time": "pre-treatment",
    }])
    result = parse_metadata(meta, GSE78220_CFG)
    assert result.loc[0, "sample_id"] == "GSM999"


def test_gse91061_uses_title_as_sample_id():
    # GSE91061 uses 'title' as sample_id_column
    meta = make_meta([{
        "title": "Pt1_Pre_AD101148-6",
        "characteristics_ch1.1.response": "PD",
        "characteristics_ch1.0.visit (pre or on treatment)": "Pre",
    }])
    result = parse_metadata(meta, GSE91061_CFG)
    assert result.loc[0, "sample_id"] == "Pt1_Pre_AD101148-6"


# ---------------------------------------------------------------------------
# missing sample_id_column raises clearly
# ---------------------------------------------------------------------------


def test_missing_sample_id_column_raises():
    meta = make_meta([{
        "wrong_column": "GSM001",
        "characteristics_ch1.1.anti-pd-1 response": "Complete Response",
    }])
    with pytest.raises(KeyError, match="Missing sample_id_column"):
        parse_metadata(meta, GSE78220_CFG)


# ---------------------------------------------------------------------------
# dataset_accession is attached
# ---------------------------------------------------------------------------


def test_dataset_accession_is_set():
    meta = make_meta([{
        "geo_accession": "GSM001",
        "characteristics_ch1.1.anti-pd-1 response": "Complete Response",
        "characteristics_ch1.12.biopsy time": "pre-treatment",
    }])
    result = parse_metadata(meta, GSE78220_CFG)
    assert result.loc[0, "dataset_accession"] == "GSE78220"


# ---------------------------------------------------------------------------
# output schema
# ---------------------------------------------------------------------------


def test_output_columns_are_exactly_the_expected_set():
    meta = make_meta([{
        "geo_accession": "GSM001",
        "characteristics_ch1.1.anti-pd-1 response": "Complete Response",
        "characteristics_ch1.12.biopsy time": "pre-treatment",
    }])
    result = parse_metadata(meta, GSE78220_CFG)
    expected = {
        "sample_id", "response_raw", "response_label",
        "timepoint_raw", "timepoint", "dataset_accession",
    }
    assert set(result.columns) == expected


def test_multiple_rows_all_processed():
    meta = make_meta([
        {
            "geo_accession": "GSM001",
            "characteristics_ch1.1.anti-pd-1 response": "Complete Response",
            "characteristics_ch1.12.biopsy time": "pre-treatment",
        },
        {
            "geo_accession": "GSM002",
            "characteristics_ch1.1.anti-pd-1 response": "Progressive Disease",
            "characteristics_ch1.12.biopsy time": "on-treatment",
        },
    ])
    result = parse_metadata(meta, GSE78220_CFG)
    assert len(result) == 2
    assert result.loc[0, "response_label"] == "responder"
    assert result.loc[1, "response_label"] == "non_responder"
    assert result.loc[0, "timepoint"] == "baseline"
    assert result.loc[1, "timepoint"] == "on-treatment"


# ---------------------------------------------------------------------------
# whitespace handling
# ---------------------------------------------------------------------------


def test_whitespace_in_response_value_is_stripped():
    meta = make_meta([{
        "geo_accession": "GSM001",
        "characteristics_ch1.1.anti-pd-1 response": "  Complete Response  ",
        "characteristics_ch1.12.biopsy time": "pre-treatment",
    }])
    result = parse_metadata(meta, GSE78220_CFG)
    # stripped raw value should match mapping
    assert result.loc[0, "response_label"] == "responder"


def test_empty_string_response_treated_as_null():
    meta = make_meta([{
        "geo_accession": "GSM001",
        "characteristics_ch1.1.anti-pd-1 response": "   ",  # blank
        "characteristics_ch1.12.biopsy time": "pre-treatment",
    }])
    result = parse_metadata(meta, GSE78220_CFG)
    assert pd.isna(result.loc[0, "response_raw"])