select
    gene_id,
    response_label,
    count(distinct sample_id) as sample_count,
    avg(log2_expression) as mean_log2_expression,
    stddev_samp(log2_expression) as std_log2_expression
from {{ ref('int_baseline_log_expression') }}
group by 1, 2