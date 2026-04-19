from pathlib import Path
import matplotlib.pyplot as plt

from analysis.utils import load_baseline_log_expression, load_top_differential_genes


FIGURE_PATH = Path("outputs/figures/gse78220_candidate_gene_boxplots.png")
TABLE_PATH = Path("outputs/tables/gse78220_top5_differential_genes.csv")


def main():
    expr_df = load_baseline_log_expression()
    top_genes_df = load_top_differential_genes(limit=5)
    genes = top_genes_df["gene_id"].tolist()

    plot_df = expr_df[expr_df["gene_id"].isin(genes)].copy()

    TABLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    top_genes_df.to_csv(TABLE_PATH, index=False)

    fig, axes = plt.subplots(len(genes), 1, figsize=(8, 3 * len(genes)))

    if len(genes) == 1:
        axes = [axes]

    for ax, gene in zip(axes, genes):
        gene_df = plot_df[plot_df["gene_id"] == gene]

        responder_vals = gene_df.loc[
            gene_df["response_label"] == "responder", "log2_expression"
        ].values
        non_responder_vals = gene_df.loc[
            gene_df["response_label"] == "non_responder", "log2_expression"
        ].values

        ax.boxplot([responder_vals, non_responder_vals], labels=["responder", "non_responder"])
        ax.set_title(gene)
        ax.set_ylabel("log2(expression + 1)")

    fig.tight_layout()
    fig.savefig(FIGURE_PATH, dpi=200)
    plt.close(fig)

    print("Saved figure:", FIGURE_PATH)
    print("Saved gene table:", TABLE_PATH)


if __name__ == "__main__":
    main()