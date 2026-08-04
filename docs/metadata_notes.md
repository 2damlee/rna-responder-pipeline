# Metadata Notes

## GSE78220

Status: inspected

### phenotype_data overview
- shape: (28, 58)
- sample identifier column: `geo_accession`

### response field
Selected field:
- `characteristics_ch1.1.anti-pd-1 response`

Observed raw values:
- `Progressive Disease`
- `Partial Response`
- `Complete Response`

Parsing decision:
- `Complete Response` -> `responder`
- `Partial Response` -> `responder`
- `Progressive Disease` -> `non_responder`

Notes:
- Mapping is restricted to observed labels only.

### timepoint field
Primary field:
- `characteristics_ch1.12.biopsy time`

Fallback fields:
- `characteristics_ch1.13.biopsy time`
- `characteristics_ch1.11.biopsy time`

Observed raw values:
- `pre-treatment`
- `on-treatment`

Parsing decision:
- `pre-treatment` -> `baseline`
- `on-treatment` remains non-baseline

Notes:
- biopsy time values appear across multiple sparse columns in phenotype_data
- parser uses ordered fallback lookup across the configured timepoint fields

### sample id decision
Selected field:
- `geo_accession`

Rationale:
- standard GEO sample identifier format (`GSM...`)
- expected join key for expression matrix columns

### implementation notes
- use explicit mapping only
- do not use substring matching for response labels
- keep registry-driven field selection
- use fallback fields only where missingness is observed

### expression extraction note
- `GEOparse.pivot_samples("VALUE")` failed with `KeyError: 'ID_REF'`
- this indicates the GEO sample tables for GSE78220 do not match the standard pivot_samples expectation
- next step is to inspect GSM sample table structure directly before choosing the extraction path
- expression matrix may need to be loaded from supplementary processed files instead of sample tables

### expression source decision
- GEO family SOFT for GSE78220 does not contain usable sample or platform tables for expression extraction
- `GEOparse.pivot_samples()` is not valid for this dataset
- expression data should be loaded from the processed supplementary file on the GEO series record
- selected expression source: `GSE78220_PatientFPKM.xlsx`
- metadata and expression should be joined after inspecting the Excel sheet structure and sample identifier format

### expression join key decision
- supplementary file columns use the format `{patient_label}.{timepoint_token}`
- observed examples:
  - `Pt1.baseline`
  - `Pt16.OnTx`
  - `Pt27A.baseline`
- metadata join key should be built from:
  - `title` as patient label
  - normalized timepoint token:
    - `baseline` -> `baseline`
    - `on-treatment` -> `OnTx`
  

---

## GSE91061

Status: inspected

### phenotype_data overview
- shape: (109, 35)
- sample identifier column: `geo_accession`
- 109 rows = multiple timepoints per patient (Pre + On treatment)

### response field
Selected field:
- `characteristics_ch1.1.response`

Observed raw values:
- `PD` (Progressive Disease)
- `SD` (Stable Disease)
- `UNK` (Unknown)

Parsing decision:
- `PD` → `non_responder`
- `SD` → excluded (ambiguous — not clearly responder or non_responder)
- `UNK` → excluded (no response data)

Note: This dataset has no "responder" equivalent label. Only `PD` maps to
a usable label. This means the baseline cohort will be smaller than expected.
Check if the full response label set includes additional values (CR/PR) after
downloading the expression file and re-inspecting.

### timepoint field
Selected field:
- `characteristics_ch1.0.visit (pre or on treatment)`

Observed raw values:
- `Pre` → baseline
- `On` → on-treatment (excluded from baseline cohort)

### sample id decision
Selected field:
- `geo_accession`

### expression source
- GEOparse `pivot_samples("VALUE")`: NOT available (`data_row_count: 0`)
- Supplementary file: `BMS038_118Sample.hg19KnownGene.fpkm.csv.gz`
- Download: automated via `download_expression_file()` in `gse91061.py`
- URL: https://ftp.ncbi.nlm.nih.gov/geo/series/GSE91nnn/GSE91061/suppl/

### join key decision
Expression columns use Pt-style labels (e.g. `Pt1_Pre_AD101148-6`),
which match the metadata `title` field — NOT `geo_accession`.
Join path:
  expression.title_key → metadata.title → metadata.geo_accession (sample_id)
---

## gene_id namespace audit (T1)

Question: do GSE78220 and GSE91061 use the same gene_id identifier system?
This matters because `mart_top_differential_genes` inner-joins the two response
groups on `gene_id`. If the two datasets use different namespaces, the join
behaves very differently than the model name suggests.

### Confirmed
- **GSE78220 `gene_id` = HGNC gene symbols.** Verified from committed outputs
  (`outputs/tables/gse78220_top5_differential_genes.csv`,
  `gse78220_heatmap_matrix_top30.csv`): values are `SNORD33`, `CDH1`, `CRYAB`,
  `FABP7`, `LOC283352`, `MIR4442`, etc. — symbol format, not numeric IDs.

### Not confirmed in this environment
- **GSE91061 `gene_id` = unknown, suspected different namespace.** The
  supplementary file is `...hg19KnownGene.fpkm.csv.gz`. "KnownGene" strongly
  suggests UCSC KnownGene / Entrez-style identifiers rather than HGNC symbols,
  but this was NOT directly inspected (no committed gene_id for GSE91061; the
  expression file was not re-downloaded).

### How to confirm (run locally, where the parquets exist)
```python
import pandas as pd
a = set(pd.read_parquet("data/processed/gse78220/baseline_long.parquet")["gene_id"])
b = set(pd.read_parquet("data/processed/gse91061/baseline_long.parquet")["gene_id"])
print("gse78220 sample:", list(a)[:5])
print("gse91061 sample:", list(b)[:5])
print(f"overlap: {len(a & b)}  (of {len(a)} vs {len(b)})")
```

### Consequence for the current mart (either way, the fix is the same)
- responder rows only ever come from GSE78220 (GSE91061 is non_responder-only),
  so `responder_mean` is always GSE78220.
- `mart_top_differential_genes` inner-joins responder × non_responder on gene_id.
- **If overlap ~ 0 (suspected):** only GSE78220 symbols survive the join, and
  their `non_responder_mean` is also GSE78220-only. GSE91061 contributes nothing
  to the mart — it is silently dropped despite appearing in staging/intermediate.
  The committed numbers are therefore already GSE78220-only.
- **If overlap is large:** `non_responder_mean` for overlapping genes mixes both
  studies. Because FPKM normalization differs across studies, that mean is not a
  valid responder-vs-non_responder comparison.

Fix (T2): group `int_gene_group_stats` by `dataset_accession` as well, and join
within a single dataset in the mart, so the comparison is never implicitly
cross-study. This makes the single-study scope explicit instead of silent.

### Confirmed result (run locally, 2026)
- GSE78220 gene_id sample: PRODH2, LCN2, LINC00870 (HGNC symbols)
- GSE91061 gene_id sample: 100874086, 57590, 283748 (numeric Entrez IDs)
- overlap: 0 of the two gene_id sets
- => Case A: the two namespaces do not overlap. GSE91061 never contributed rows
  to mart_top_differential_genes; committed numbers were already GSE78220-only.
  The T2 fix makes this scope explicit and prevents future pooling.
