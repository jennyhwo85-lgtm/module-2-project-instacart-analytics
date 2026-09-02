# Instacart ELT Dataflow and Mart Data Dictionary

## Purpose

This document explains how data moves from the downloaded CSV files to the final analytical tables. It is intended as a simple guide for contributors and as the reference for the mart-layer data dictionary.

The design follows a layered ELT pattern:

```text
CSV files
   ↓
Raw DuckDB tables
   ↓
dbt staging models
   ↓
dbt intermediate models
   ↓
dbt mart tables
   ↓
Jupyter analysis / Streamlit dashboard
```

## Why use layers?

Each layer has one clear responsibility. This makes the pipeline easier to understand, test, rebuild, and change.

| Layer | Main question answered | What belongs here? |
|---|---|---|
| Raw | What did the source file contain? | CSV data loaded with minimal changes |
| Staging | Can each source table be used consistently? | Renaming, type casting, simple standardisation |
| Intermediate | How do the source tables fit together? | Unions, joins, reusable derived fields |
| Mart | What should analysts query? | Business-ready facts, dimensions, and metrics |

## 1. Raw layer

The Python ingestion script reads the six CSV files from `data/` and creates tables in `warehouse/instacart.duckdb`.

| Raw table | Source file | Grain |
|---|---|---|
| `raw_orders` | `orders.csv` | One row per order |
| `raw_products` | `products.csv` | One row per product |
| `raw_aisles` | `aisles.csv` | One row per aisle |
| `raw_departments` | `departments.csv` | One row per department |
| `raw_order_products_prior` | `order_products__prior.csv` | One row per product in a prior order |
| `raw_order_products_train` | `order_products__train.csv` | One row per product in a training order |

Raw tables are retained as the reproducible source-of-truth. Do not apply business logic here.

## 2. Staging layer

Staging models read raw tables through dbt sources. They are normally views and perform light, row-level standardisation:

- cast identifiers and measures to explicit types;
- use consistent column names;
- preserve source meaning;
- add `source_eval_set` to distinguish prior and train order-item records.

Staging models do not create the star schema and should not contain complex joins or business metrics.

Current staging models:

```text
raw_orders                  → stg_orders
raw_products                → stg_products
raw_aisles                  → stg_aisles
raw_departments             → stg_departments
raw_order_products_prior    → stg_order_products_prior
raw_order_products_train    → stg_order_products_train
```

## 3. Intermediate layer

The intermediate layer combines and enriches staging models. This is the layer that prepares reusable data for more than one mart; it is not the final business-facing schema.

### Required intermediate models

#### `int_order_products`

Combines `stg_order_products_prior` and `stg_order_products_train` with `union all`.

**Grain:** one row per product in an observed prior or train order.

Important columns:

- `order_id`
- `product_id`
- `add_to_cart_order`
- `reordered`
- `source_eval_set`

#### `int_order_items_enriched` (missing model to add)

Joins `int_order_products` to `stg_orders` and `stg_products`. It should also join aisle and department staging models when descriptive names are required.

**Grain:** one row per product in an observed order.

This model creates the reusable row-level foundation for `fact_order_items`, product analysis, basket analysis, and reorder metrics.

Recommended relationships:

```text
int_order_products.order_id  → stg_orders.order_id
int_order_products.product_id → stg_products.product_id
stg_products.aisle_id        → stg_aisles.aisle_id
stg_products.department_id   → stg_departments.department_id
```

## 4. Mart layer and star schema

The mart layer is the published interface for notebooks, dashboards, and stakeholders. It contains dimensions for descriptive context and facts for measurable events.

```text
dim_users       ─┐
dim_orders      ─┤
dim_products    ─┤
dim_aisles      ─┤── fact_order_items
dim_departments ─┘
```

### `fact_order_items`

**Business meaning:** one observed product line within one order.

**Grain:** one row per `(order_id, product_id)` in the prior or train data.

| Column | Type | Definition | Source / derivation |
|---|---|---|---|
| `order_id` | integer | Unique order identifier | Order-product data |
| `user_id` | integer | Customer identifier | Joined from `stg_orders` |
| `product_id` | integer | Product identifier | Order-product data |
| `aisle_id` | integer | Aisle identifier | Joined from `stg_products` |
| `department_id` | integer | Department identifier | Joined from `stg_products` |
| `order_number` | integer | Customer's sequence number for this order | `stg_orders` |
| `order_dow` | integer | Day-of-week code, 0–6 | `stg_orders` |
| `order_hour_of_day` | integer | Hour of day, 0–23 | `stg_orders` |
| `days_since_prior_order` | double | Days since the customer's previous order; null for first order | `stg_orders` |
| `add_to_cart_order` | integer | Position at which the product was added to the basket | Order-product data |
| `reordered` | integer | 1 if previously purchased by the user, otherwise 0 | Order-product data |
| `source_eval_set` | varchar | `prior` or `train` source indicator | Added during staging/intermediate transformation |

There is no price, quantity, currency, or calendar date in this dataset. Therefore this fact table supports order and product behaviour analysis, not revenue reporting or true monthly sales trends.

### `dim_orders`

**Grain:** one row per order.

| Column | Definition |
|---|---|
| `order_id` | Unique order identifier; primary key |
| `user_id` | Customer who placed the order |
| `eval_set` | Dataset role: `prior`, `train`, or `test` |
| `order_number` | Customer's order sequence |
| `order_dow` | Day-of-week code, 0–6 |
| `order_hour_of_day` | Hour slot, 0–23 |
| `days_since_prior_order` | Days since previous order, when available |

### `dim_products`

**Grain:** one row per product.

| Column | Definition |
|---|---|
| `product_id` | Product identifier; primary key |
| `product_name` | Product description |
| `aisle_id` | Related aisle identifier |
| `department_id` | Related department identifier |

### `dim_aisles`

**Grain:** one row per aisle.

| Column | Definition |
|---|---|
| `aisle_id` | Aisle identifier; primary key |
| `aisle_name` | Aisle description |

### `dim_departments`

**Grain:** one row per department.

| Column | Definition |
|---|---|
| `department_id` | Department identifier; primary key |
| `department_name` | Department description |

### `dim_users`

This can be a derived dimension because the source has no separate customer file.

**Grain:** one row per `user_id`.

Recommended fields:

| Column | Definition |
|---|---|
| `user_id` | Customer identifier; primary key |
| `observed_order_count` | Number of orders represented in the data |
| `observed_item_count` | Number of product lines in observed prior/train orders |
| `reordered_item_count` | Number of observed product lines where `reordered = 1` |
| `reorder_rate` | `reordered_item_count / observed_item_count`; null when no items exist |

## 5. Data-quality expectations

At minimum, add dbt tests for:

- non-null and unique primary keys in dimensions;
- non-null `order_id` and `product_id` in the fact table;
- relationships from fact keys to their dimensions;
- `reordered` values restricted to 0 or 1;
- `order_dow` between 0 and 6;
- `order_hour_of_day` between 0 and 23;
- positive `add_to_cart_order` values;
- `source_eval_set` restricted to `prior` and `train` in the fact table.

## 6. Team rule for adding models

Before creating a model, write down its grain in one sentence. For example:

> `fact_order_items` contains one row per product in one observed order.

Then document its inputs, key columns, and tests. This prevents accidental duplication when joins are added.

## 7. Core measurable activity (directly from fact_order_items)

1. number of orders;
2. basket size;
3. most frequently ordered products;
4. department and aisle activity;
5. reorder rate;
6. order patterns by day of week;
7. order patterns by hour of day;
8. customer purchase behaviour.
