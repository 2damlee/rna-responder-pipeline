select
    gene_id,
    sample_id,
    expression,
    ln(expression + 1.0) / ln(2.0) as log2_expression,
    response_label,
    timepoint,
    dataset_accession
from {{ ref('stg_gse78220_expression') }}
where timepoint = 'baseline'
  and response_label in ('responder', 'non_responder')