# Contributing

## Adding a new GEO dataset

The parser is designed so that adding a new dataset requires no changes
to `parse_metadata.py`. The shared parsing logic reads field names and
value mappings from `config/datasets.yml` at runtime.

Follow these steps to add a new dataset:

---

### Step 1. Inspect the metadata

```python
import GEOparse

gse = GEOparse.get_GEO("GSExxxxx", destdir="./data/raw/geo")
meta = gse.phenotype_data

print(meta.columns.tolist())
for col in meta.columns:
    print(col, meta[col].dropna().unique()[:3].tolist())
```

---

### Step 2. Record findings in `docs/metadata_notes.md`

Add a section for the new dataset following the existing format:
- Which column holds the response label
- Observed raw values (e.g. "R", "NR", "PD", "Complete Response")
- Which column holds the timepoint
- Whether `pivot_samples("VALUE")` works or a supplementary file is needed
- How expression column names relate to sample identifiers

This record is what justifies the parsing rules in `datasets.yml`.

---

### Step 3. Add an entry to `config/datasets.yml`

```yaml
- accession: GSExxxxx
  source_type: geo
  expression_value_column: VALUE
  sample_id_column: geo_accession       # or 'title' if columns use Pt-style names
  response_label_fields:
    - characteristics_ch1.x.response    # actual column name from Step 1
  timepoint_fields:
    - characteristics_ch1.y.timepoint   # actual column name from Step 1
  response_mapping:
    RawValue1: responder                # exact match only — no substring matching
    RawValue2: non_responder
  baseline_values:
    - pre                               # exact raw value that means pre-treatment
```

**Important:** `response_mapping` uses exact string matching. Do not use
partial strings — "R" will not match "responder" or "CR". Always check
the actual raw values from Step 1 before writing this section.

---

### Step 4. Create `pipeline/tasks/<accession_lower>.py`

Implement two functions:

```python
def build_baseline_dataset() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Returns (parsed_meta, expr_long, baseline, qc_summary)."""
    ...

def save_baseline_outputs(parsed_meta, expr_long, baseline, qc_summary) -> None:
    """Saves parquets to data/processed/<accession>/ and QC CSV to outputs/tables/."""
    ...
```

Use `gse91061.py` as a reference if the expression file uses Pt-style
column names (title-based join). Use `gse78220.py` if the join key
requires constructing a patient+timepoint token.

---

### Step 5. Register in `pipeline/flows/ingest_geo.py`

Add the new accession to the `task_build_baseline_dataset` and
`task_save_baseline_outputs` dispatch blocks, and to the `--accession`
choices in the argument parser.

---

### Step 6. Extend the dbt staging model

Add a `union all` block to `dbt/models/staging/stg_gse78220_expression.sql`
and add the corresponding var to `dbt/dbt_project.yml`:

```yaml
vars:
  processed_dir_gse78220: "data/processed/gse78220"
  processed_dir_gse91061: "data/processed/gse91061"
  processed_dir_gsexxxxx: "data/processed/gsexxxxx"  # add this
```

---

### Step 7. Run and verify

```bash
python -m pipeline.flows.ingest_geo --accession GSExxxxx
cat outputs/tables/gsexxxxx_qc_summary.csv
python -m pytest -v
dbt run --project-dir dbt
dbt test --project-dir dbt
```

Check that `baseline_unique_samples` in the QC summary is greater than 0.
If it is 0, re-examine the timepoint and response parsing rules.