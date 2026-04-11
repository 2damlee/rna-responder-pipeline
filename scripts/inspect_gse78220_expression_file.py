from pathlib import Path
import pandas as pd


FILE_PATH = Path("data/raw/geo/GSE78220_PatientFPKM.xlsx")


def main():
    if not FILE_PATH.exists():
        raise FileNotFoundError(f"Missing file: {FILE_PATH}")

    excel_file = pd.ExcelFile(FILE_PATH)

    print("\n=== sheet names ===")
    print(excel_file.sheet_names)

    for sheet_name in excel_file.sheet_names:
        print(f"\n=== sheet: {sheet_name} ===")
        df = pd.read_excel(FILE_PATH, sheet_name=sheet_name)

        print("shape:", df.shape)
        print("columns:", df.columns.tolist())
        print(df.head(10))

        # 너무 길어지지 않게 첫 번째 시트만 자세히 보고 끝내도 됨
        break


if __name__ == "__main__":
    main()