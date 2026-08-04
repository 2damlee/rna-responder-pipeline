-- Group statistics are computed PER DATASET.
-- Without dataset_accession in the grouping key, a gene's non_responder mean
-- would silently pool samples from different studies (different FPKM
-- normalization), making responder-vs-non_responder differences
-- indistinguishable from study/batch differences.
select
    dataset_accession,
    gene_id,
    response_label,
    count(distinct sample_id) as sample_count,
    avg(log2_expression) as mean_log2_expression,
    stddev_samp(log2_expression) as std_log2_expression
from {{ ref('int_baseline_log_expression') }}
group by 1, 2, 3