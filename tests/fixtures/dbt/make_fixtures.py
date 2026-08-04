"""Generate tiny baseline_long parquets used to run `dbt build` without network.

Run from repo root:  python tests/fixtures/dbt/make_fixtures.py

The scenario deliberately reproduces the cross-study trap the T2 fix guards
against: both datasets share gene_id "CDH1", and GSE91061 is non_responder-only.

Expected results after the fix (per-dataset group stats + within-dataset join):
  int_gene_group_stats:
    GSE78220 CDH1 responder      mean log2 = 3.5
    GSE78220 CDH1 non_responder  mean log2 = 1.5   <- NOT pooled with GSE91061
    GSE78220 SNORD33 responder   mean log2 = 1.0
    GSE78220 SNORD33 non_responder mean log2 = 7.0
    GSE91061 CDH1 non_responder  mean log2 = 7.0   <- kept separate, visible
  mart_top_differential_genes (responder vs non_responder, within dataset):
    GSE78220 SNORD33  abs_mean_diff = 6.0
    GSE78220 CDH1     abs_mean_diff = 2.0
    GSE91061          -> no rows (no responders)

If group stats regressed to pooling, GSE78220 CDH1 non_responder would become
mean(log2 of {1,3,63,255}) = 4.25 and abs_mean_diff would be 0.75.
"""

from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent

COLS = ["gene_id", "sample_id", "expression", "response_label", "timepoint", "dataset_accession"]


def main() -> None:
    ds1 = pd.DataFrame(
        [
            # SNORD33: responder {1,1} -> log2(2)=1.0 ; non_resp {63,255} -> {6,8}=7.0
            ("SNORD33", "R1", 1, "responder", "baseline", "GSE78220"),
            ("SNORD33", "R2", 1, "responder", "baseline", "GSE78220"),
            ("SNORD33", "N1", 63, "non_responder", "baseline", "GSE78220"),
            ("SNORD33", "N2", 255, "non_responder", "baseline", "GSE78220"),
            # CDH1: responder {7,15} -> {3,4}=3.5 ; non_resp {1,3} -> {1,2}=1.5
            ("CDH1", "R1", 7, "responder", "baseline", "GSE78220"),
            ("CDH1", "R2", 15, "responder", "baseline", "GSE78220"),
            ("CDH1", "N1", 1, "non_responder", "baseline", "GSE78220"),
            ("CDH1", "N2", 3, "non_responder", "baseline", "GSE78220"),
        ],
        columns=COLS,
    )
    # GSE91061: reuses gene_id CDH1 (worst case), non_responder only
    ds2 = pd.DataFrame(
        [
            ("CDH1", "M1", 63, "non_responder", "baseline", "GSE91061"),
            ("CDH1", "M2", 255, "non_responder", "baseline", "GSE91061"),
        ],
        columns=COLS,
    )

    (HERE / "gse78220").mkdir(parents=True, exist_ok=True)
    (HERE / "gse91061").mkdir(parents=True, exist_ok=True)
    ds1.to_parquet(HERE / "gse78220" / "baseline_long.parquet", index=False)
    ds2.to_parquet(HERE / "gse91061" / "baseline_long.parquet", index=False)
    print("wrote fixtures under", HERE)


if __name__ == "__main__":
    main()