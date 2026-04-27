from pathlib import Path
import yaml
import pandas as pd
import GEOparse

from pipeline.tasks.parse_metadata import parse_metadata
from pipeline.utils.config_loader import load_dataset_config


ACCESSION = "GSE78220"
EXPRESSION_FILE = Path("data/raw/geo/GSE78220_PatientFPKM.xlsx")
EXPRESSION_SHEET = "FPKM"


def load_gse(accession: str = ACCESSION):
    geo_dir = Path("data/raw/geo")
    geo_dir.mkdir(parents=True, exist_ok=True)
    return GEOparse.get_GEO(geo=accession, destdir=str(geo_dir))


def build_expression_sample_key(patient_label: str, timepoint: str) -> str | None:
    if pd.isna(patient_label) or pd.isna(timepoint):
        return None

    patient_label = str(patient_label).strip()

    if timepoint == "baseline":
        timepoint_token = "baseline"
    elif timepoint == "on-treatment":
        timepoint_token = "OnTx"
    else:
        return None

    return f"{patient_label}.{timepoint_token}"


def load_expression_from_excel() -> pd.DataFrame:
    if not EXPRESSION_FILE.exists():
        raise FileNotFoundError(
            f"Missing expression file: {EXPRESSION_FILE}"
        )

    expr = pd.read_excel(EXPRESSION_FILE, sheet_name=EXPRESSION_SHEET)

    if "Gene" not in expr.columns:
        raise KeyError("Expected 'Gene' column in supplementary expression file.")

    expr = expr.rename(columns={"Gene": "gene_id"})

    expr_long = expr.melt(
        id_vars="gene_id",
        var_name="expression_sample_key",
        value_name="expression",
    )

    expr_long["gene_id"] = expr_long["gene_id"].astype(str).str.strip()
    expr_long["expression_sample_key"] = expr_long["expression_sample_key"].astype(str).str.strip()
    expr_long["expression"] = pd.to_numeric(expr_long["expression"], errors="coerce")

    return expr_long


def prepare_metadata_for_join(meta: pd.DataFrame, dataset_cfg: dict) -> pd.DataFrame:
    parsed = parse_metadata(meta, dataset_cfg).copy()

    parsed["patient_label"] = meta["title"].astype(str).str.strip().values
    parsed["expression_sample_key"] = parsed.apply(
        lambda row: build_expression_sample_key(
            row["patient_label"],
            row["timepoint"],
        ),
        axis=1,
    )

    return parsed


def validate_join_keys(parsed_meta: pd.DataFrame, expr_long: pd.DataFrame) -> dict:
    none_key_rows = parsed_meta[parsed_meta["expression_sample_key"].isna()]

    if not none_key_rows.empty:
        print(
            f"WARNING: {len(none_key_rows)} samples have no expression_sample_key "
            f"(timepoint not resolved). These will be excluded from the join."
        )

    valid_meta = parsed_meta.dropna(subset=["expression_sample_key"])
    expression_keys = set(expr_long["expression_sample_key"].dropna().unique())

    unmatched = valid_meta[
        ~valid_meta["expression_sample_key"].isin(expression_keys)
    ]

    if not unmatched.empty:
        raise ValueError(
            f"Join key mismatch: {len(unmatched)} metadata keys not found "
            f"in expression file.\n"
            f"{unmatched[['sample_id', 'expression_sample_key']].to_string(index=False)}"
        )

    return {
        "none_key_count": len(none_key_rows),
        "valid_key_count": len(valid_meta),
        "unmatched_count": 0,
    }

def build_qc_summary(
    expr_long: pd.DataFrame,
    parsed_meta: pd.DataFrame,
    merged: pd.DataFrame,
    baseline: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "metric": [
                "parsed_metadata_rows",
                "parsed_metadata_unique_samples",
                "parsed_metadata_unique_expression_keys",
                "expression_long_rows",
                "expression_unique_expression_keys",
                "expression_unique_genes",
                "merged_rows",
                "merged_unique_samples",
                "merged_null_response_label_rows",
                "merged_null_timepoint_rows",
                "baseline_rows",
                "baseline_unique_samples",
                "baseline_unique_genes",
                "baseline_null_expression_rows",
            ],
            "value": [
                len(parsed_meta),
                parsed_meta["sample_id"].nunique(),
                parsed_meta["expression_sample_key"].nunique(),
                len(expr_long),
                expr_long["expression_sample_key"].nunique(),
                expr_long["gene_id"].nunique(),
                len(merged),
                merged["sample_id"].nunique(),
                merged["response_label"].isna().sum(),
                merged["timepoint"].isna().sum(),
                len(baseline),
                baseline["sample_id"].nunique(),
                baseline["gene_id"].nunique(),
                baseline["expression"].isna().sum(),
            ],
        }
    )


def build_baseline_dataset() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    dataset_cfg = load_dataset_config(ACCESSION)
    gse = load_gse()

    meta = gse.phenotype_data.copy()
    parsed_meta = prepare_metadata_for_join(meta, dataset_cfg)
    expr_long = load_expression_from_excel()

    validation = validate_join_keys(parsed_meta, expr_long)
    print(f"Join key validation: {validation}")

    merged = expr_long.merge(
        parsed_meta[
            [
                "sample_id",
                "patient_label",
                "expression_sample_key",
                "response_label",
                "timepoint",
                "dataset_accession",
            ]
        ],
        on="expression_sample_key",
        how="left",
    )

    baseline = merged[
        (merged["timepoint"] == "baseline")
        & (merged["response_label"].isin(["responder", "non_responder"]))
        & (merged["expression"].notna())
    ].copy()

    qc_summary = build_qc_summary(expr_long, parsed_meta, merged, baseline)
    return parsed_meta, expr_long, baseline, qc_summary


def save_baseline_outputs(
    parsed_meta: pd.DataFrame,
    expr_long: pd.DataFrame,
    baseline: pd.DataFrame,
    qc_summary: pd.DataFrame,
) -> None:
    out_dir = Path("data/processed/gse78220")
    out_dir.mkdir(parents=True, exist_ok=True)

    output_tables_dir = Path("outputs/tables")
    output_tables_dir.mkdir(parents=True, exist_ok=True)

    parsed_meta.to_parquet(out_dir / "parsed_metadata.parquet", index=False)
    expr_long.to_parquet(out_dir / "expression_long.parquet", index=False)
    baseline.to_parquet(out_dir / "baseline_long.parquet", index=False)
    qc_summary.to_csv(output_tables_dir / "gse78220_qc_summary.csv", index=False)