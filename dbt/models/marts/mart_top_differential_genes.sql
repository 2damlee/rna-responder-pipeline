-- Genes ranked by absolute difference in mean log2 expression between
-- responders and non-responders, computed WITHIN a single dataset.
--
-- The responder and non_responder means are joined on (gene_id,
-- dataset_accession), so every row compares two groups from the SAME study.
-- Cross-study comparison is intentionally impossible here: FPKM normalization
-- differs across studies, and the two datasets use different gene_id
-- namespaces (GSE78220 = HGNC symbols, GSE91061 = hg19KnownGene). See
-- docs/metadata_notes.md (gene_id namespace audit) and docs/architecture.md.
--
-- Consequence with the current data: only GSE78220 has both response groups,
-- so only GSE78220 produces rows. GSE91061 (non_responder only) produces none.
-- That is correct and now explicit, rather than the group means being silently
-- polluted.

with responder as (
    select
        dataset_accession,
        gene_id,
        mean_log2_expression as responder_mean
    from {{ ref('int_gene_group_stats') }}
    where response_label = 'responder'
),
non_responder as (
    select
        dataset_accession,
        gene_id,
        mean_log2_expression as non_responder_mean
    from {{ ref('int_gene_group_stats') }}
    where response_label = 'non_responder'
)

select
    r.dataset_accession,
    r.gene_id,
    r.responder_mean,
    n.non_responder_mean,
    abs(r.responder_mean - n.non_responder_mean) as abs_mean_diff
from responder r
join non_responder n
    on  r.gene_id = n.gene_id
    and r.dataset_accession = n.dataset_accession
order by abs_mean_diff desc
