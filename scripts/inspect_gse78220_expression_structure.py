from pathlib import Path
import GEOparse


ACCESSION = "GSE78220"


def main():
    geo_dir = Path("./data/raw/geo")
    geo_dir.mkdir(parents=True, exist_ok=True)

    gse = GEOparse.get_GEO(geo=ACCESSION, destdir=str(geo_dir))

    print("\n=== GSE accession ===")
    print(gse.get_accession())

    print("\n=== platform ids ===")
    print(list(gse.gpls.keys()))

    print("\n=== sample count ===")
    print(len(gse.gsms))

    first_sample_name = list(gse.gsms.keys())[0]
    first_sample = gse.gsms[first_sample_name]

    print("\n=== first sample accession ===")
    print(first_sample_name)

    print("\n=== first sample metadata keys ===")
    print(list(first_sample.metadata.keys()))

    print("\n=== first sample table shape ===")
    print(first_sample.table.shape)

    print("\n=== first sample table columns ===")
    print(first_sample.table.columns.tolist())

    print("\n=== first sample table head ===")
    print(first_sample.table.head())

    print("\n=== platform table shape ===")
    for gpl_id, gpl in gse.gpls.items():
        print(gpl_id, gpl.table.shape)
        print(gpl.table.columns.tolist()[:20])
        print(gpl.table.head())
        break

    print("\n=== sample table availability summary ===")
    for gsm_id, gsm in list(gse.gsms.items())[:5]:
        print(f"{gsm_id}: shape={gsm.table.shape}, columns={gsm.table.columns.tolist()}")


if __name__ == "__main__":
    main()