# Reference Only - Not the Team's Official Submission

These files were built by Lai Yoke during self-study/exploration ahead of the team's official ELT, dbt, and dashboard work. They demonstrate one possible end-to-end approach (Meltano to BigQuery, dbt-style feature engineering in pandas, Parquet export, validation) but they are not the team's finished deliverable.

## What's here

- meltano.yml - Full Extract+Load config: tap-duckdb (local DuckDB) to target-bigquery. Only the extractor half overlaps with the team's official DuckDB pipeline; the loader half belongs to the ELT/dbt workstream.
- Feature Engineering.ipynb - Builds all five star-schema tables in pandas, including every engineered feature, and saves them as CSVs.
- export_dim_product_parquet.sql - BigQuery EXPORT DATA statement for dim_product.
- export_final_tables_parquet.sh - Shell script exporting all five star-schema tables to Parquet via bq extract.
- read_dim_product_parquet.py - Validates the exported dim_product Parquet file with PyArrow.

## Why this is kept separate

Per the team's task assignment (root README.md, Team and Task Assignment):
- Lai Yoke and Jenny Hwo own the local DuckDB pipeline and validation.
- Hui Min and Benedict own ELT/data cleaning in GCP, dbt, EDA, and the dashboard.

The files above go beyond the local DuckDB scope. They're kept here so work isn't lost and can be reused, but should not be treated as the team's final dbt/ELT implementation without review. Hui Min and Benedict are welcome to reference or build on this logic.
