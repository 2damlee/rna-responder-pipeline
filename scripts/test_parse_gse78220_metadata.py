from pathlib import Path
import yaml
import GEOparse

from pipeline.tasks.parse_metadata import parse_metadata


def load_dataset_config(accession: str) -> dict:
    with open("config/datasets.yml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    for dataset in config["datasets"]:
        if dataset["accession"] == accession:
            return dataset

    raise ValueError(f"Dataset config not found: {accession}")


def main():
    accession = "GSE78220"
    geo_dir = Path("./data/raw/geo")
    geo_dir.mkdir(parents=True, exist_ok=True)

    gse = GEOparse.get_GEO(geo=accession, destdir=str(geo_dir))
    meta = gse.phenotype_data.copy()

    dataset_cfg = load_dataset_config(accession)
    parsed = parse_metadata(meta, dataset_cfg)

    print("\n=== parsed metadata preview ===")
    print(parsed.head(10))

    print("\n=== response_label counts ===")
    print(parsed["response_label"].value_counts(dropna=False))

    print("\n=== timepoint counts ===")
    print(parsed["timepoint"].value_counts(dropna=False))

    print("\n=== missing summary ===")
    print("missing response_label:", parsed["response_label"].isna().sum())
    print("missing timepoint:", parsed["timepoint"].isna().sum())

    print("\n=== rows with missing timepoint ===")
    print(
        parsed.loc[parsed["timepoint"].isna(), ["sample_id", "timepoint_raw"]]
        .sort_values("sample_id")
    )


if __name__ == "__main__":
    main()