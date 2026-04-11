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
- No `Stable Disease` value was observed in the initial inspection output.
- Mapping is restricted to observed labels only.

### timepoint field
Selected field:
- `characteristics_ch1.12.biopsy time`

Observed raw values:
- `pre-treatment`
- `on-treatment`

Parsing decision:
- `pre-treatment` -> `baseline`
- `on-treatment` remains non-baseline

### sample id decision
Selected field:
- `geo_accession`

Rationale:
- standard GEO sample identifier format (`GSM...`)
- likely join key for expression matrix columns

### implementation notes
- use explicit mapping only
- do not use substring matching for response labels
- start with a single primary field for response and timepoint
- add fallback fields only if later validation shows missingness