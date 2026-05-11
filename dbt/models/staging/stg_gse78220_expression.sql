-- dbt/models/staging/stg_gse78220_expression.sql
-- Reads baseline parquets from all configured datasets and unions into
-- one standardized expression table.
-- Each row: gene_id x sample_id x expression, with response_label and dataset_accession.

select
    cast(gene_id         as varchar) as gene_id,
    cast(sample_id       as varchar) as sample_id,
    cast(expression      as double)  as expression,
    cast(response_label  as varchar) as response_label,
    cast(timepoint       as varchar) as timepoint,
    cast(dataset_accession as varchar) as dataset_accession
from read_parquet(
    '{{ var("processed_dir_gse78220", "data/processed/gse78220") }}/baseline_long.parquet'
)
where expression  is not null
  and gene_id     is not null
  and sample_id   is not null

union all

select
    cast(gene_id         as varchar) as gene_id,
    cast(sample_id       as varchar) as sample_id,
    cast(expression      as double)  as expression,
    cast(response_label  as varchar) as response_label,
    cast(timepoint       as varchar) as timepoint,
    cast(dataset_accession as varchar) as dataset_accession
from read_parquet(
    '{{ var("processed_dir_gse91061", "data/processed/gse91061") }}/baseline_long.parquet'
)
where expression  is not null
  and gene_id     is not null
  and sample_id   is not null