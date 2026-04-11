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