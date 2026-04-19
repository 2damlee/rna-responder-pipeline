from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from analysis.utils import load_baseline_log_expression


FIGURE_PATH = Path("outputs/figures/gse78220_pca_top500_variable_genes.png")
TABLE_PATH = Path("outputs/tables/gse78220_pca_coordinates.csv")


def main():
    df = load_baseline_log_expression()

    expr = df.pivot_table(
        index="sample_id",
        columns="gene_id",
        values="log2_expression",
        aggfunc="mean",
    ).fillna(0.0)

    labels = (
        df[["sample_id", "response_label"]]
        .drop_duplicates()
        .set_index("sample_id")
        .loc[expr.index]
    )

    gene_var = expr.var(axis=0)
    top_genes = gene_var.nlargest(500).index
    expr_filtered = expr[top_genes]

    X_scaled = StandardScaler().fit_transform(expr_filtered)

    pca = PCA(n_components=2)
    components = pca.fit_transform(X_scaled)

    pca_df = pd.DataFrame(
        components,
        index=expr_filtered.index,
        columns=["PC1", "PC2"],
    ).join(labels)

    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    TABLE_PATH.parent.mkdir(parents=True, exist_ok=True)

    pca_df.to_csv(TABLE_PATH, index=True)

    fig, ax = plt.subplots(figsize=(8, 6))

    for label in ["responder", "non_responder"]:
        subset = pca_df[pca_df["response_label"] == label]
        ax.scatter(subset["PC1"], subset["PC2"], label=label)

        for sample_id, row in subset.iterrows():
            ax.annotate(sample_id, (row["PC1"], row["PC2"]), fontsize=8)

    ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0] * 100:.1f}%)")
    ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1] * 100:.1f}%)")
    ax.set_title("GSE78220 baseline PCA (top 500 variable genes)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURE_PATH, dpi=200)
    plt.close(fig)

    print("Explained variance ratio:", pca.explained_variance_ratio_)
    print("Saved figure:", FIGURE_PATH)
    print("Saved coordinates:", TABLE_PATH)


if __name__ == "__main__":
    main()