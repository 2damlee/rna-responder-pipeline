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


def build_expression_sample_key(title: str, timepoint: str) -> str | None:
    if pd.isna(title) or pd.isna(timepoint):
        return None

    patient_label = str(title).strip()

    if timepoint == "baseline":
        timepoint_token = "baseline"
    elif timepoint == "on-treatment":
        timepoint_token = "OnTx"
    else:
        return None

    return f"{patient_label}.{timepoint_token}"


def main():
    dataset_cfg = load_dataset_config(ACCESSION)

    gse = GEOparse.get_GEO(geo=ACCESSION, destdir="data/raw/geo")
    meta = gse.phenotype_data.copy()

    parsed = parse_metadata(meta, dataset_cfg).copy()
    parsed["patient_label"] = meta["title"].astype(str).str.strip().values
    parsed["expression_sample_key"] = parsed.apply(
        lambda row: build_expression_sample_key(
            row["patient_label"],
            row["timepoint"],
        ),
        axis=1,
    )

    expr_df = pd.read_excel(EXPRESSION_FILE, sheet_name="FPKM")
    expression_keys = set(expr_df.columns[1:])

    parsed["expression_key_found"] = parsed["expression_sample_key"].isin(expression_keys)

    print("\n=== metadata join key preview ===")
    print(
        parsed[
            [
                "sample_id",
                "patient_label",
                "timepoint",
                "expression_sample_key",
                "expression_key_found",
            ]
        ]
        .sort_values("sample_id")
    )

    print("\n=== join key match summary ===")
    print(parsed["expression_key_found"].value_counts(dropna=False))

    print("\n=== unmatched rows ===")
    print(
        parsed.loc[
            ~parsed["expression_key_found"],
            ["sample_id", "patient_label", "timepoint", "expression_sample_key"]
        ]
        .sort_values("sample_id")
    )


if __name__ == "__main__":
    main()