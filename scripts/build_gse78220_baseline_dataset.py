from pipeline.tasks.gse78220 import build_baseline_dataset, save_baseline_outputs


def main():
    parsed_meta, expr_long, baseline, qc_summary = build_baseline_dataset()
    save_baseline_outputs(parsed_meta, expr_long, baseline, qc_summary)

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