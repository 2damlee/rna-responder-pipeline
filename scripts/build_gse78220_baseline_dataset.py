from pathlib import Path
import yaml
import pandas as pd
import GEOparse

from pipeline.tasks.parse_metadata import parse_metadata


ACCESSION = "GSE78220"
EXPRESSION_FILE = Path("data/raw/geo/GSE78220_PatientFPKM.xlsx")


def load_dataset_config(accession: str) -> dict:
    with open("config/datasets.yml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    for dataset in config["datasets"]:
        if dataset["accession"] == accession:
            return dataset

    raise ValueError(f"Dataset config not found: {accession}")


def load_gse(accession: str):
    geo_dir = Path("./data/raw/geo")
    geo_dir.mkdir(parents=True, exist_ok=True)
    return GEOparse.get_GEO(geo=accession, destdir=str(geo_dir))


def load_expression_from_excel() -> pd.DataFrame:
    if not EXPRESSION_FILE.exists():
        raise FileNotFoundError(
            f"Missing expression file: {EXPRESSION_FILE}. "
            "Run scripts/download_gse78220_expression_file.py first."
        )

    # inspection 결과 보고 sheet_name 조정
    df = pd.read_excel(EXPRESSION_FILE)

    # inspection 결과 보고 gene id 컬럼명 조정
    first_col = df.columns[0]
    df = df.rename(columns={first_col: "gene_id"})

    expr_long = df.melt(
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

    # GSE78220에서는 title이 Pt1, Pt2... 형태로 보였음
    parsed["expression_sample_key"] = meta["title"].astype(str).str.strip().values

    return parsed


def build_qc_summary(expr_long, parsed_meta, merged, baseline) -> pd.DataFrame:
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


def main():
    dataset_cfg = load_dataset_config(ACCESSION)
    gse = load_gse(ACCESSION)

    meta = gse.phenotype_data.copy()
    parsed_meta = prepare_metadata_for_join(meta, dataset_cfg)

    expr_long = load_expression_from_excel()

    merged = expr_long.merge(
        parsed_meta[
            [
                "sample_id",
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

    out_dir = Path("data/processed/gse78220")
    out_dir.mkdir(parents=True, exist_ok=True)

    output_tables_dir = Path("outputs/tables")
    output_tables_dir.mkdir(parents=True, exist_ok=True)

    parsed_meta.to_parquet(out_dir / "parsed_metadata.parquet", index=False)
    expr_long.to_parquet(out_dir / "expression_long.parquet", index=False)
    baseline.to_parquet(out_dir / "baseline_long.parquet", index=False)

    qc_summary = build_qc_summary(expr_long, parsed_meta, merged, baseline)
    qc_summary.to_csv(output_tables_dir / "gse78220_qc_summary.csv", index=False)

    print("\n=== join key summary ===")
    print("metadata expression keys:", parsed_meta["expression_sample_key"].nunique())
    print("expression keys:", expr_long["expression_sample_key"].nunique())

    print("\n=== parsed metadata summary ===")
    print(parsed_meta["response_label"].value_counts(dropna=False))
    print(parsed_meta["timepoint"].value_counts(dropna=False))

    print("\n=== baseline summary ===")
    print("baseline rows:", len(baseline))
    print("baseline samples:", baseline["sample_id"].nunique())
    print("baseline genes:", baseline["gene_id"].nunique())
    print(
        baseline[["sample_id", "response_label"]]
        .drop_duplicates()["response_label"]
        .value_counts(dropna=False)
    )


if __name__ == "__main__":
    main()