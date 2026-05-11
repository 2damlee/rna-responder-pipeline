from __future__ import annotations

import urllib.request
from pathlib import Path

import pandas as pd
import GEOparse

from pipeline.tasks.parse_metadata import parse_metadata
from pipeline.utils.config_loader import load_dataset_config


ACCESSION = "GSE91061"

EXPRESSION_FILE = Path(
    "data/raw/geo/gse91061/BMS038_118Sample.hg19KnownGene.fpkm.csv.gz"
)

EXPRESSION_URL = (
    "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE91nnn/GSE91061/suppl/"
    "GSE91061_BMS038109Sample.hg19KnownGene.fpkm.csv.gz"
)


def load_gse(accession: str = ACCESSION):
    geo_dir = Path("data/raw/geo")
    geo_dir.mkdir(parents=True, exist_ok=True)
    return GEOparse.get_GEO(geo=accession, destdir=str(geo_dir), silent=True)


def download_expression_file() -> None:
    if EXPRESSION_FILE.exists():
        print(f"Expression file already exists: {EXPRESSION_FILE}")
        return
    EXPRESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading expression file from:\n  {EXPRESSION_URL}")
    urllib.request.urlretrieve(EXPRESSION_URL, EXPRESSION_FILE)
    print(f"Download complete: {EXPRESSION_FILE}")


def load_expression_from_supplementary() -> pd.DataFrame:
    """
    Load FPKM expression matrix from supplementary gz file.

    Expression columns use Pt-style labels (e.g. 'Pt1_Pre_AD101148-6'),
    which match the metadata 'title' field used as sample_id in this dataset.

    Returns long-format DataFrame: gene_id, sample_id, expression
    """
    if not EXPRESSION_FILE.exists():
        raise FileNotFoundError(
            f"Missing expression file: {EXPRESSION_FILE}\n"
            f"Run download_expression_file() first, or download manually from:\n"
            f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE91061"
        )

    expr_wide = pd.read_csv(
        EXPRESSION_FILE,
        compression="gzip",
        index_col=0,
    )

    expr_wide.index = expr_wide.index.astype(str).str.strip()
    expr_wide.index.name = "gene_id"

    expr_long = (
        expr_wide.reset_index()
        .melt(id_vars="gene_id", var_name="sample_id", value_name="expression")
    )

    expr_long["gene_id"] = expr_long["gene_id"].astype(str).str.strip()
    expr_long["sample_id"] = expr_long["sample_id"].astype(str).str.strip()
    expr_long["expression"] = pd.to_numeric(
        expr_long["expression"], errors="coerce"
    )

    return expr_long


def validate_sample_overlap(
    parsed_meta: pd.DataFrame,
    expr_long: pd.DataFrame,
) -> dict:
    meta_samples = set(parsed_meta["sample_id"].dropna())
    expr_samples = set(expr_long["sample_id"].dropna())

    matched = meta_samples & expr_samples
    only_meta = meta_samples - expr_samples
    only_expr = expr_samples - meta_samples

    if only_meta:
        print(
            f"WARNING: {len(only_meta)} metadata samples not in expression. "
            f"First 5: {sorted(only_meta)[:5]}"
        )
    if only_expr:
        print(
            f"INFO: {len(only_expr)} expression columns not in metadata. "
            f"First 5: {sorted(only_expr)[:5]}"
        )

    return {
        "meta_samples": len(meta_samples),
        "expr_samples": len(expr_samples),
        "matched_samples": len(matched),
        "only_in_meta": len(only_meta),
        "only_in_expr": len(only_expr),
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
                "expression_long_rows",
                "expression_unique_samples",
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
                len(expr_long),
                expr_long["sample_id"].nunique(),
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


def build_baseline_dataset() -> tuple[
    pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame
]:
    dataset_cfg = load_dataset_config(ACCESSION)
    gse = load_gse()

    meta = gse.phenotype_data.copy()
    parsed_meta = parse_metadata(meta, dataset_cfg)
    # parsed_meta["sample_id"] = title value (Pt1_Pre_AD101148-6)
    # which matches expression column names directly

    download_expression_file()
    expr_long = load_expression_from_supplementary()
    # expr_long["sample_id"] = Pt-style label, same as parsed_meta["sample_id"]

    overlap = validate_sample_overlap(parsed_meta, expr_long)
    print(f"Sample overlap validation: {overlap}")

    merged = expr_long.merge(
        parsed_meta[[
            "sample_id", "response_label", "timepoint", "dataset_accession"
        ]],
        on="sample_id",
        how="left",
    )

    baseline = merged[
        (merged["timepoint"] == "baseline")
        & (merged["response_label"].isin(["responder", "non_responder"]))
        & (merged["expression"].notna())
    ].copy()

    print(
        f"Baseline cohort: {baseline['sample_id'].nunique()} samples, "
        f"{baseline['gene_id'].nunique()} genes, "
        f"{len(baseline)} rows"
    )

    qc_summary = build_qc_summary(expr_long, parsed_meta, merged, baseline)
    return parsed_meta, expr_long, baseline, qc_summary


def save_baseline_outputs(
    parsed_meta: pd.DataFrame,
    expr_long: pd.DataFrame,
    baseline: pd.DataFrame,
    qc_summary: pd.DataFrame,
) -> None:
    out_dir = Path("data/processed/gse91061")
    out_dir.mkdir(parents=True, exist_ok=True)

    output_tables_dir = Path("outputs/tables")
    output_tables_dir.mkdir(parents=True, exist_ok=True)

    parsed_meta.to_parquet(out_dir / "parsed_metadata.parquet", index=False)
    expr_long.to_parquet(out_dir / "expression_long.parquet", index=False)
    baseline.to_parquet(out_dir / "baseline_long.parquet", index=False)
    qc_summary.to_csv(
        output_tables_dir / "gse91061_qc_summary.csv", index=False
    )
    print(f"Saved outputs to {out_dir}")