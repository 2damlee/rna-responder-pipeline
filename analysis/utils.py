from pathlib import Path
import duckdb
import pandas as pd


DUCKDB_PATH = Path("data/curated/rna_responder.duckdb")


def get_connection():
    if not DUCKDB_PATH.exists():
        raise FileNotFoundError(f"DuckDB file not found: {DUCKDB_PATH}")
    return duckdb.connect(str(DUCKDB_PATH), read_only=True)


def load_baseline_log_expression() -> pd.DataFrame:
    con = get_connection()
    try:
        query = """
        select
            gene_id,
            sample_id,
            log2_expression,
            response_label,
            dataset_accession
        from int_baseline_log_expression
        """
        return con.execute(query).df()
    finally:
        con.close()


def load_top_differential_genes(limit: int = 30) -> pd.DataFrame:
    con = get_connection()
    try:
        query = f"""
        select
            gene_id,
            responder_mean,
            non_responder_mean,
            abs_mean_diff
        from mart_top_differential_genes
        order by abs_mean_diff desc
        limit {limit}
        """
        return con.execute(query).df()
    finally:
        con.close()