# Data Dictionary — Data Cleaning Layer

This data dictionary documents the six Instacart datasets processed by the Data Cleaning notebook. It covers the data from the BigQuery raw tables through validation and data-type standardisation.

## 1. Data lineage

```text
BigQuery raw tables
    → Pandas Data Cleaning notebook
```

The notebook loads the six BigQuery raw tables using private environment variables, confirms that the downloaded row counts match BigQuery, profiles data quality, and standardises numeric types.

## 2. Dataset summary

| Original dataset | BigQuery raw table | Grain | Verified rows |
|---|---|---|---:|
| `aisles.csv` | `raw_aisles` | One row per aisle | 134 |
| `departments.csv` | `raw_departments` | One row per department | 21 |
| `products.csv` | `raw_products` | One row per product | 49,688 |
| `orders.csv` | `raw_orders` | One row per order | 3,421,083 |
| `order_products__prior.csv` | `raw_order_products_prior` | One product within one prior order | 32,434,489 |
| `order_products__train.csv` | `raw_order_products_train` | One product within one train order | 1,384,617 |

No records are removed during data cleaning, so the validated datasets retain the verified source row counts.

## 3. `aisles`

**Grain:** One row per aisle.

| Column | Cleaned type | Key | Description | Cleaning and validity rule |
|---|---|---|---|---|
| `aisle_id` | Integer (`int64`) | Primary key | Unique aisle identifier. | Required, unique, and converted to integer. |
| `aisle` | String/text | — | Aisle name. | Required text. Identifier and category fields are not subjected to numerical outlier treatment. |

## 4. `departments`

**Grain:** One row per department.

| Column | Cleaned type | Key | Description | Cleaning and validity rule |
|---|---|---|---|---|
| `department_id` | Integer (`int64`) | Primary key | Unique department identifier. | Required, unique, and converted to integer. |
| `department` | String/text | — | Department name. | Required text. Identifier and category fields are not subjected to numerical outlier treatment. |

## 5. `products`

**Grain:** One row per product.

| Column | Cleaned type | Key | Description | Cleaning and validity rule |
|---|---|---|---|---|
| `product_id` | Integer (`int64`) | Primary key | Unique product identifier. | Required, unique, and converted to integer. |
| `product_name` | String/text | — | Product name. | Required text and retained as supplied. |
| `aisle_id` | Integer (`int64`) | Foreign key → `aisles.aisle_id` | Identifier of the aisle containing the product. | Required, converted to integer, and expected to reference a valid aisle. |
| `department_id` | Integer (`int64`) | Foreign key → `departments.department_id` | Identifier of the department containing the product. | Required, converted to integer, and expected to reference a valid department. |

## 6. `orders`

**Grain:** One row per order.

| Column | Cleaned type | Key | Description | Cleaning and validity rule |
|---|---|---|---|---|
| `order_id` | Integer (`int64`) | Primary key | Unique order identifier. | Required, unique, and converted to integer. |
| `user_id` | Integer (`int64`) | User identifier | Identifies the customer who placed the order. | Required and converted to integer. |
| `eval_set` | String/text | — | Indicates whether the order belongs to the `prior`, `train`, or `test` set. | Required; accepted values are `prior`, `train`, and `test`. |
| `order_number` | Integer (`int64`) | — | Sequential order number for the customer, beginning with 1. | Required and at least 1. High values are retained because they represent frequent customers. |
| `order_dow` | Integer (`int64`) | — | Encoded day-of-week value. | Required and between 0 and 6. No weekday name is assumed. |
| `order_hour_of_day` | Integer (`int64`) | — | Hour when the order was placed. | Required and between 0 and 23. |
| `days_since_prior_order` | Float (`float64`) | — | Days since the customer's preceding order. A value of 30 represents 30 or more days. | Null for a customer's first order because no preceding order exists; otherwise expected between 0 and 30. Meaningful first-order `NaN` values are retained. |

## 7. `order_products_prior`

**Grain:** One product within one prior order.

**Composite key:** (`order_id`, `product_id`)

| Column | Cleaned type | Key | Description | Cleaning and validity rule |
|---|---|---|---|---|
| `order_id` | Integer (`int64`) | Composite key; foreign key → `orders.order_id` | Identifier of the prior order. | Required, converted to integer, and expected to reference an order in the `prior` evaluation set. |
| `product_id` | Integer (`int64`) | Composite key; foreign key → `products.product_id` | Identifier of the product included in the order. | Required, converted to integer, and expected to reference a valid product. |
| `add_to_cart_order` | Integer (`int64`) | — | Sequence in which the product was added to the basket. | Required and at least 1. High values are retained because they represent valid large baskets. |
| `reordered` | Integer (`int64`, 0/1) | — | Indicates whether the customer had purchased the product previously. | Required binary value: `0` = not reordered; `1` = reordered. |

## 8. `order_products_train`

**Grain:** One product within one train order.

**Composite key:** (`order_id`, `product_id`)

| Column | Cleaned type | Key | Description | Cleaning and validity rule |
|---|---|---|---|---|
| `order_id` | Integer (`int64`) | Composite key; foreign key → `orders.order_id` | Identifier of the train order. | Required, converted to integer, and expected to reference an order in the `train` evaluation set. |
| `product_id` | Integer (`int64`) | Composite key; foreign key → `products.product_id` | Identifier of the product included in the order. | Required, converted to integer, and expected to reference a valid product. |
| `add_to_cart_order` | Integer (`int64`) | — | Sequence in which the product was added to the basket. | Required and at least 1. High values are retained because they represent valid large baskets. |
| `reordered` | Integer (`int64`, 0/1) | — | Indicates whether the customer had purchased the product previously. | Required binary value: `0` = not reordered; `1` = reordered. |

## 9. Data-cleaning checks and treatments

| Check or treatment | Implementation in the Data Cleaning notebook |
|---|---|
| Source connection | Reads the BigQuery project and raw dataset from private `.env` variables. |
| Source completeness | Compares each downloaded Pandas table count with its corresponding BigQuery raw-table count. |
| Shape review | Reviews the row and column counts of all six datasets. |
| Descriptive profiling | Reviews descriptive statistics for all six datasets using `describe(include="all")` to identify unusual distributions and values. |
| Missing values | Profiles missing values, non-null counts, and missing percentages for every column. |
| Duplicate records | Checks exact duplicates, primary-key duplicates, and duplicate (`order_id`, `product_id`) combinations. |
| Numeric conversion | Uses `pd.to_numeric`; required integer columns use `errors="raise"` and are stored as `int64`. |
| First-order missing values | Converts `days_since_prior_order` to `float64` while retaining valid first-order `NaN` values. |
| Statistical outliers | Reviews `order_number`, `days_since_prior_order`, and `add_to_cart_order` using IQR and box plots. |
| Row deletion | Does not remove records because the reviewed unusual values represent valid customer and basket behaviour. |

### Outlier review recorded in the notebook

| Field | Potential IQR outliers | Interpretation and treatment |
|---|---:|---|
| `orders.order_number` above 50 | 216,870 | Frequent customers; retained. |
| `order_products_prior.add_to_cart_order` above 23 | 1,357,124 (4.18%) | Products in large baskets; retained. |
| `order_products_train.add_to_cart_order` of 26 or more | 50,853 (3.67%) | Products in large baskets; retained. |

## 10. Raw-data relationships

| Parent column | Cardinality | Child column |
|---|---|---|
| `aisles.aisle_id` | One aisle to many products | `products.aisle_id` |
| `departments.department_id` | One department to many products | `products.department_id` |
| `orders.order_id` | One prior order to many order-item records | `order_products_prior.order_id` |
| `orders.order_id` | One train order to many order-item records | `order_products_train.order_id` |
| `products.product_id` | One product to many prior order-item records | `order_products_prior.product_id` |
| `products.product_id` | One product to many train order-item records | `order_products_train.product_id` |

## 11. Scope boundary

This document covers the Data Cleaning stage only. It does not document downstream analytical tables, customer classifications, or derived dashboard measures.
