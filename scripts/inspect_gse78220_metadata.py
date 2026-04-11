from pathlib import Path
import pandas as pd
import GEOparse


def preview_unique_values(meta: pd.DataFrame, max_unique: int = 20) -> None:
    print("\n=== Candidate categorical columns: unique values preview ===")
    for col in meta.columns:
        if meta[col].dtype == "object":
            values = meta[col].dropna().astype(str).str.strip().unique().tolist()
            print(f"\n[{col}]")
            if len(values) <= max_unique:
                print(values)
            else:
                print(values[:max_unique], "...")


def preview_keyword_matched_columns(meta: pd.DataFrame) -> None:
    keywords = [
        "response",
        "respond",
        "responder",
        "non",
        "time",
        "point",
        "treat",
        "baseline",
        "pre",
    ]

    matched_cols = [col for col in meta.columns if any(k in col.lower() for k in keywords)]

    print("\n=== Keyword-matched columns ===")
    if not matched_cols:
        print("No columns matched keywords directly.")
        return

    for col in matched_cols:
        values = meta[col].dropna().astype(str).str.strip().unique().tolist()
        print(f"\n[{col}]")
        if len(values) <= 30:
            print(values)
        else:
            print(values[:30], "...")


def main():
    geo_dir = Path("./data/raw/geo")
    geo_dir.mkdir(parents=True, exist_ok=True)

    print("Downloading/loading GSE78220 ...")
    gse = GEOparse.get_GEO(geo="GSE78220", destdir=str(geo_dir))

    print("\n=== GSE-level metadata keys ===")
    print(list(gse.metadata.keys()))

    meta = gse.phenotype_data.copy()

    print("\n=== phenotype_data shape ===")
    print(meta.shape)

    print("\n=== phenotype_data columns ===")
    for i, col in enumerate(meta.columns, start=1):
        print(f"{i:02d}. {col}")

    print("\n=== phenotype_data head (transposed, first 5 samples) ===")
    print(meta.head(5).T)

    preview_unique_values(meta)
    preview_keyword_matched_columns(meta)

    if "geo_accession" in meta.columns:
        print("\n=== geo_accession preview ===")
        print(meta["geo_accession"].head(10).tolist())
    else:
        print("\n=== geo_accession preview ===")
        print("Column 'geo_accession' not found.")

    out_dir = Path("./outputs/metadata_inspection")
    out_dir.mkdir(parents=True, exist_ok=True)

    meta.to_csv(out_dir / "gse78220_phenotype_data_full.csv", index=True)
    meta.head(10).T.to_csv(out_dir / "gse78220_phenotype_data_head_transposed.csv")

    print("\nSaved files:")
    print(out_dir / "gse78220_phenotype_data_full.csv")
    print(out_dir / "gse78220_phenotype_data_head_transposed.csv")


if __name__ == "__main__":
    main()