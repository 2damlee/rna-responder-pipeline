from pathlib import Path
from urllib.request import urlretrieve


URL = "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE78nnn/GSE78220/suppl/GSE78220_PatientFPKM.xlsx"
OUTPUT_PATH = Path("data/raw/geo/GSE78220_PatientFPKM.xlsx")


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if OUTPUT_PATH.exists():
        print(f"File already exists: {OUTPUT_PATH}")
        return

    print(f"Downloading {URL}")
    urlretrieve(URL, OUTPUT_PATH)
    print(f"Saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()