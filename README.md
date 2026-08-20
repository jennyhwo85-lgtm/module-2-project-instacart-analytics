# Instacart Market Basket Analysis

NTU SCTP Module 2 group project. A small, trustworthy analytics system that turns Instacart's raw CSV files into tested, business-ready warehouse tables, a reproducible Python/dbt pipeline, and an executive-facing dashboard/deck.

## 1. Business Problem

Instacart processes millions of customer orders across thousands of products. However, the original data is distributed across six separate CSV files, making it difficult for business users to analyse ordering patterns, customer behaviour, and product demand efficiently.

Without an organised analytical data model, Instacart may find it difficult to answer important questions such as when customers place orders, what a typical order contains, which products are purchased and reordered most frequently, and how customers differ in their purchasing behaviour.

This project develops a data pipeline, analytical data warehouse, and interactive dashboard that transform the raw Instacart data into structured and reusable business information, supporting workforce planning, product availability, customer engagement, and repeat-order recommendations.

## 2. Project Objectives

1. Ingest the six Instacart source files into BigQuery to provide centralised and scalable data storage.
2. Clean and validate the raw data by checking missing values, duplicate records, data types, and logical inconsistencies.
3. Transform the source data into a star-schema-based analytical model containing customer, product, order-time, order, and order-item tables.
4. Engineer customer, order, and product features such as basket size, customer order frequency, reorder rate, average order gap, and customer segment.
5. Use Python and pandas to analyse ordering patterns, customer purchasing behaviour, and product demand.
6. Develop a Streamlit dashboard that communicates the findings through KPI cards, charts, filters, and business implications.

> **Important data boundary:** Instacart provides no calendar dates, prices, revenue, or customer demographics. This project therefore reports *behaviour* metrics — not monthly sales or monetary customer value — and documents this limitation throughout.

## 3. How This Maps to the Assignment Brief

The assignment brief recommends monthly sales trends, top-selling products, and customer segmentation by purchasing behaviour. These were adapted to what the Instacart dataset actually contains — see [`docs/assignment_brief.md`](docs/assignment_brief.md) for the original brief and [`docs/README.md`](docs/README.md) §3 for the full mapping table.

| Dashboard page | Business question |
|---|---|
| 1. Overview / Order Activity | When do customers place orders, and what is the typical order size? |
| 2. Customer Segments | What customer purchasing segments exist, and how do their behaviours differ? |
| 3. Product Analysis | Which products/departments/aisles have the highest demand and reorder rate? |

## 4. Architecture

Local-source data is ingested via **Meltano**, loaded into **BigQuery**, transformed and tested with **dbt**, orchestrated with **Dagster**, and analysed via **Jupyter** / visualised in **Streamlit / Power BI**.

![Pipeline architecture](docs/pipeline_architecture.jpeg)

## 5. Star Schema

| Table | Grain | Purpose |
|---|---|---|
| `dim_product` | One row per product | Product name plus aisle and department hierarchy |
| `dim_user` | One row per customer | Customer identifier and engineered behavioural features |
| `dim_order_slot` | One row per day-of-week/hour combination | Supports time-pattern analysis (168 possible slots) |
| `fact_order` | One row per order | Order sequence, customer, timing, and order-level metrics |
| `fact_order_item` | One row per product within an order | Cart position, reorder flag, prior/train source |

Full field-level definitions: [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md)
Design rationale: [`docs/STAR_SCHEMA_README.md`](docs/STAR_SCHEMA_README.md)
Current ERD (in progress, being reviewed against the data dictionary): [`docs/star_schema_erd.jpg`](docs/star_schema_erd.jpg)

## 6. Data Cleaning and Feature Engineering

Full write-up of profiling, missing-value handling, duplicate/uniqueness checks, referential-integrity checks, and outlier handling: [`docs/DATA_CLEANING_README.md`](docs/DATA_CLEANING_README.md)

Key engineered features: `basket_size`, `customer_reorder_rate`, `average_order_gap`, `customer_segment`, `slot_key`, `time_band`, `product_reorder_rate`. Full definitions and calculations: [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md) §4.

## 7. Team and Task Assignment

| Owner(s) | Responsibility |
|---|---|
| Lai Yoke, Jenny Hwo | Data warehouse (star schema, BigQuery), GitHub repo |
| Hui Min, Benedict | EDA, dashboard, ELT / data cleaning (in GCP), dbt |
| Wei Xiang | Integration review, presentation, audience Q&A |

## 8. Repository Structure

```text
instacart-analytics/
├── README.md                # this file
├── docs/                    # architecture decisions, data dictionary, diagrams, assignment brief
├── data/                    # dataset location / download instructions (raw CSVs not committed)
├── src/                     # Python ingestion and quality-check scripts
├── warehouse/               # generated warehouse artefacts (ignored)
├── dbt_project/             # staging, intermediate, mart SQL models and tests
├── notebooks/               # numbered, reproducible analysis notebooks
├── tests/                   # Python tests where dbt tests are not sufficient
├── github/workflows/        # pull-request quality workflow
└── presentation/            # final slide deck and speaker notes
```

Generated databases, raw CSVs, notebook caches, and secrets must not be committed. Code, model SQL, test definitions, documentation, and a reproducible dependency file must be committed.

## 9. Status / Open Items

- [ ] Reconcile `dim_user` engineered-feature fields, `slot_key` type, `time_band`/`day_part` naming, `reordered` type, and `fact_order_item.item_count` between the ERD and `docs/DATA_DICTIONARY.md` (tracked in that file §6).
- [ ] Confirm dataset placement/download instructions in `data/README.md`.
- [ ] Repo scaffold created 2026-08-19; dbt models, ingestion scripts, and notebooks to follow.
