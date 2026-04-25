select
    cast(gene_id as varchar) as gene_id,
    cast(sample_id as varchar) as sample_id,
    cast(expression as double) as expression,
    cast(response_label as varchar) as response_label,
    cast(timepoint as varchar) as timepoint,
    cast(dataset_accession as varchar) as dataset_accession
from read_parquet('{{ var("processed_dir", "data/processed/gse78220") }}/baseline_long.parquet')
where expression is not null
  and gene_id is not null
  and sample_id is not null