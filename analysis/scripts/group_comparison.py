"""
Responder vs Non-responder group comparison.

Visualizes mean log2 expression of top differential genes as a scatter plot
(non-responder mean on x-axis, responder mean on y-axis).
Genes above the diagonal are higher in responders; below the diagonal are
higher in non-responders.

Data source: mart_top_differential_genes (built by dbt)
"""
from __future__ import annotations

from pathlib import Path

import duckdb
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
import numpy as np

DUCKDB_PATH = Path("data/curated/rna_responder.duckdb")
FIGURE_PATH = Path("outputs/figures/gse78220_group_scatter.png")
TABLE_PATH = Path("outputs/tables/gse78220_group_comparison.csv")
TOP_N = 50
LABEL_N = 8


def load_group_stats() -> pd.DataFrame:
    if not DUCKDB_PATH.exists():
        raise FileNotFoundError(
            f"DuckDB file not found: {DUCKDB_PATH}\n"
            "Run dbt first: dbt run --project-dir dbt"
        )

    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    df = con.execute(f"""
        SELECT
            gene_id,
            responder_mean,
            non_responder_mean,
            abs_mean_diff,
            CASE
                WHEN responder_mean > non_responder_mean THEN 'higher_in_responder'
                ELSE 'higher_in_non_responder'
            END AS direction
        FROM mart_top_differential_genes
        ORDER BY abs_mean_diff DESC
        LIMIT {TOP_N}
    """).df()
    con.close()
    return df


def plot_group_scatter(df: pd.DataFrame) -> None:
    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)

    color_map = {
        "higher_in_responder":     "#2563EB",
        "higher_in_non_responder": "#DC2626",
    }
    colors = df["direction"].map(color_map)

    fig, ax = plt.subplots(figsize=(8, 8))

    ax.scatter(
        df["non_responder_mean"],
        df["responder_mean"],
        c=colors,
        alpha=0.75,
        s=55,
        edgecolors="white",
        linewidths=0.4,
        zorder=3,
    )

    # Diagonal — no difference line
    all_vals = pd.concat([df["non_responder_mean"], df["responder_mean"]])
    lo, hi = all_vals.min() * 0.95, all_vals.max() * 1.05
    ax.plot([lo, hi], [lo, hi], color="grey", linestyle="--",
            linewidth=1, alpha=0.5, zorder=1, label="no difference")
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)

    # Label top N genes by abs_mean_diff
    for _, row in df.nlargest(LABEL_N, "abs_mean_diff").iterrows():
        ax.annotate(
            str(row["gene_id"]),
            xy=(row["non_responder_mean"], row["responder_mean"]),
            xytext=(5, 4),
            textcoords="offset points",
            fontsize=7,
            alpha=0.85,
        )

    # Legend
    patches = [
        mpatches.Patch(color="#2563EB", label="Higher in responder"),
        mpatches.Patch(color="#DC2626", label="Higher in non-responder"),
    ]
    ax.legend(handles=patches, loc="upper left", fontsize=9)

    ax.set_xlabel("Non-responder mean log2 expression", fontsize=11)
    ax.set_ylabel("Responder mean log2 expression", fontsize=11)
    ax.set_title(
        f"GSE78220 — Responder vs Non-responder\n"
        f"Top {TOP_N} differential genes (log2 FPKM)",
        fontsize=12,
    )
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.2, zorder=0)

    plt.tight_layout()
    plt.savefig(FIGURE_PATH, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Saved: {FIGURE_PATH}")


def save_table(df: pd.DataFrame) -> None:
    TABLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(TABLE_PATH, index=False)
    print(f"Saved: {TABLE_PATH}")


def main() -> None:
    print(f"Loading top {TOP_N} differential genes from DuckDB mart...")
    df = load_group_stats()
    print(f"  Loaded {len(df)} genes")
    print(f"  Higher in responder:     {(df['direction'] == 'higher_in_responder').sum()}")
    print(f"  Higher in non-responder: {(df['direction'] == 'higher_in_non_responder').sum()}")

    plot_group_scatter(df)
    save_table(df)


if __name__ == "__main__":
    main()