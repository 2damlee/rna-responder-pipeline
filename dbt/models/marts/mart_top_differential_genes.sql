with responder as (
    select
        gene_id,
        mean_log2_expression as responder_mean
    from {{ ref('int_gene_group_stats') }}
    where response_label = 'responder'
),
non_responder as (
    select
        gene_id,
        mean_log2_expression as non_responder_mean
    from {{ ref('int_gene_group_stats') }}
    where response_label = 'non_responder'
)

select
    r.gene_id,
    r.responder_mean,
    n.non_responder_mean,
    abs(r.responder_mean - n.non_responder_mean) as abs_mean_diff
from responder r
join non_responder n
    on r.gene_id = n.gene_id
order by abs_mean_diff desc