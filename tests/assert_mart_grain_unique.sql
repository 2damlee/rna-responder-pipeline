select
    gene_id,
    dataset_accession,
    count(*) as n
from {{ ref('mart_top_differential_genes') }}
group by gene_id, dataset_accession
having count(*) > 1