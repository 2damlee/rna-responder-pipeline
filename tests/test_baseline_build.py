import pandas as pd

from pipeline.tasks import gse78220, gse91061


# ---------------------------------------------------------------------------
# GSE78220: join key is expression_sample_key (patient_label.timepoint token)
# ---------------------------------------------------------------------------

def _gse78220_frames():
    parsed_meta = pd.DataFrame(
        {
            "sample_id": ["GSM_A", "GSM_B", "GSM_C"],
            "patient_label": ["PtA", "PtB", "PtC"],
            "expression_sample_key": ["PtA.baseline", "PtB.baseline", "PtC.OnTx"],
            "response_label": ["responder", "non_responder", "responder"],
            "timepoint": ["baseline", "baseline", "on-treatment"],
            "dataset_accession": ["GSE78220"] * 3,
        }
    )
    # 2 genes x 3 sample keys = 6 rows; one expression value is null.
    expr_long = pd.DataFrame(
        {
            "gene_id": ["G1", "G1", "G1", "G2", "G2", "G2"],
            "expression_sample_key": [
                "PtA.baseline", "PtB.baseline", "PtC.OnTx",
                "PtA.baseline", "PtB.baseline", "PtC.OnTx",
            ],
            "expression": [10.0, 20.0, 30.0, 5.0, None, 15.0],
        }
    )
    return parsed_meta, expr_long


def test_gse78220_baseline_only_baseline_timepoint():
    parsed_meta, expr_long = _gse78220_frames()
    _, baseline, _ = gse78220.build_baseline_from_frames(parsed_meta, expr_long)
    assert (baseline["timepoint"] == "baseline").all()
    # PtC is on-treatment and must be excluded
    assert "PtC.OnTx" not in set(baseline["expression_sample_key"])


def test_gse78220_baseline_has_no_null_response_or_expression():
    parsed_meta, expr_long = _gse78220_frames()
    _, baseline, _ = gse78220.build_baseline_from_frames(parsed_meta, expr_long)
    assert baseline["response_label"].notna().all()
    assert baseline["response_label"].isin(["responder", "non_responder"]).all()
    assert baseline["expression"].notna().all()


def test_gse78220_left_join_does_not_fan_out():
    parsed_meta, expr_long = _gse78220_frames()
    merged, _, _ = gse78220.build_baseline_from_frames(parsed_meta, expr_long)
    # metadata keys are unique, so a left join must not add rows
    assert len(merged) == len(expr_long)


def test_gse78220_qc_baseline_sample_count():
    parsed_meta, expr_long = _gse78220_frames()
    _, _, qc = gse78220.build_baseline_from_frames(parsed_meta, expr_long)
    val = qc.set_index("metric")["value"]
    # baseline samples = PtA (responder) + PtB (non_responder); PtC excluded.
    # PtB/G2 is null-expression so dropped, but PtB still present via G1.
    assert val["baseline_unique_samples"] == 2
    assert val["baseline_null_expression_rows"] == 0


# ---------------------------------------------------------------------------
# GSE91061: join key is sample_id (Pt-style title), non_responder only
# ---------------------------------------------------------------------------

def _gse91061_frames():
    parsed_meta = pd.DataFrame(
        {
            "sample_id": ["Pt1_Pre", "Pt2_Pre", "Pt3_On", "Pt4_Pre"],
            "response_label": ["non_responder", "non_responder", "non_responder", None],
            "timepoint": ["baseline", "baseline", "on-treatment", "baseline"],
            "dataset_accession": ["GSE91061"] * 4,
        }
    )
    # gene ids are numeric-style strings, mirroring the real Entrez namespace
    expr_long = pd.DataFrame(
        {
            "gene_id": ["100", "100", "100", "100", "200", "200", "200", "200"],
            "sample_id": [
                "Pt1_Pre", "Pt2_Pre", "Pt3_On", "Pt4_Pre",
                "Pt1_Pre", "Pt2_Pre", "Pt3_On", "Pt4_Pre",
            ],
            "expression": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        }
    )
    return parsed_meta, expr_long


def test_gse91061_baseline_only_baseline_timepoint():
    parsed_meta, expr_long = _gse91061_frames()
    _, baseline, _ = gse91061.build_baseline_from_frames(parsed_meta, expr_long)
    assert (baseline["timepoint"] == "baseline").all()
    assert "Pt3_On" not in set(baseline["sample_id"])


def test_gse91061_excludes_null_and_non_response_labels():
    parsed_meta, expr_long = _gse91061_frames()
    _, baseline, _ = gse91061.build_baseline_from_frames(parsed_meta, expr_long)
    # Pt4 has a null response_label and must be excluded
    assert "Pt4_Pre" not in set(baseline["sample_id"])
    assert baseline["response_label"].isin(["responder", "non_responder"]).all()


def test_gse91061_left_join_does_not_fan_out():
    parsed_meta, expr_long = _gse91061_frames()
    merged, _, _ = gse91061.build_baseline_from_frames(parsed_meta, expr_long)
    assert len(merged) == len(expr_long)


def test_gse91061_qc_baseline_sample_count():
    parsed_meta, expr_long = _gse91061_frames()
    _, _, qc = gse91061.build_baseline_from_frames(parsed_meta, expr_long)
    val = qc.set_index("metric")["value"]
    # baseline samples = Pt1 + Pt2 (both non_responder, baseline). Pt3 on-tx,
    # Pt4 null-label both excluded.
    assert val["baseline_unique_samples"] == 2