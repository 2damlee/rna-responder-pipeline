from pathlib import Path
import matplotlib.pyplot as plt

from analysis.utils import load_baseline_log_expression, load_top_differential_genes


FIGURE_PATH = Path("outputs/figures/gse78220_top30_heatmap.png")
TABLE_PATH = Path("outputs/tables/gse78220_heatmap_matrix_top30.csv")


def main():
    expr_df = load_baseline_log_expression()
    top_genes = load_top_differential_genes(limit=30)["gene_id"].tolist()

    heatmap_df = expr_df[expr_df["gene_id"].isin(top_genes)].copy()

    matrix = heatmap_df.pivot_table(
        index="sample_id",
        columns="gene_id",
        values="log2_expression",
        aggfunc="mean",
    ).fillna(0.0)

    sample_labels = (
        heatmap_df[["sample_id", "response_label"]]
        .drop_duplicates()
        .set_index("sample_id")
        .loc[matrix.index]
    )

    matrix = matrix.loc[sample_labels.sort_values(["response_label"]).index]

    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    TABLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    matrix.to_csv(TABLE_PATH)

    fig, ax = plt.subplots(figsize=(12, 8))
    im = ax.imshow(matrix.values, aspect="auto")

    ax.set_xticks(range(len(matrix.columns)))
    ax.set_xticklabels(matrix.columns, rotation=90, fontsize=8)

    ax.set_yticks(range(len(matrix.index)))
    ax.set_yticklabels(matrix.index, fontsize=8)

    ax.set_title("GSE78220 baseline heatmap (top 30 differential genes)")
    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    fig.savefig(FIGURE_PATH, dpi=200)
    plt.close(fig)

    print("Saved figure:", FIGURE_PATH)
    print("Saved matrix:", TABLE_PATH)


if __name__ == "__main__":
    main()