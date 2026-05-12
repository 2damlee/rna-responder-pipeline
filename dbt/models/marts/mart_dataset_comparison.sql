-- dbt/models/marts/mart_dataset_comparison.sql
-- Cohort-level summary per dataset and response group.
-- Answers: how do GSE78220 and GSE91061 baseline cohorts differ in composition
-- and expression distribution?
--
-- This mart is the entry point for multi-study comparison.
-- GSE91061 currently has only non_responder samples (PD label only).
-- GSE78220 has both responder and non_responder.

with base as (
    select
        dataset_accession,
        response_label,
        sample_id,
        gene_id,
        log2_expression
    from {{ ref('int_baseline_log_expression') }}
),

per_dataset_group as (
    select
        dataset_accession,
        response_label,
        count(distinct sample_id)   as sample_count,
        count(distinct gene_id)     as gene_count,
        count(*)                    as total_rows,
        round(avg(log2_expression), 4)    as mean_log2_expression,
        round(stddev(log2_expression), 4) as std_log2_expression,
        round(min(log2_expression), 4)    as min_log2_expression,
        round(max(log2_expression), 4)    as max_log2_expression
    from base
    group by dataset_accession, response_label
)

select *
from per_dataset_group
order by dataset_accession, response_label