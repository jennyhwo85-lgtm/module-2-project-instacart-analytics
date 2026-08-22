# Instacart Data Cleaning and Validation

This document explains the step-by-step data-cleaning and validation process applied to the six Instacart source files before table joins, transformation, feature engineering, exploratory data analysis, and dashboard development.

The source data was generally high quality. Therefore, the cleaning process focused on validating the data and preserving meaningful customer behaviour rather than deleting records or imputing values unnecessarily.

## Source Files

The following six source files were checked separately:

- `orders.csv`
- `products.csv`
- `aisles.csv`
- `departments.csv`
- `order_products__prior.csv`
- `order_products__train.csv`

## Step 1: Load and Profile Each Source File

Each CSV file was loaded into a separate Pandas DataFrame. Its shape, column names, sample records, and data types were inspected.

| Source file | Rows | Columns |
|---|---:|---:|
| `orders.csv` | 3,421,083 | 7 |
| `products.csv` | 49,688 | 4 |
| `aisles.csv` | 134 | 2 |
| `departments.csv` | 21 | 2 |
| `order_products__prior.csv` | 32,434,489 | 4 |
| `order_products__train.csv` | 1,384,617 | 4 |

### Rationale

Profiling confirms that each file was loaded correctly and that no rows or columns were accidentally lost. Inspecting the files separately also avoids creating one unnecessarily large merged table before understanding the grain and purpose of each source.

## Step 2: Verify Column Names and Data Types

The data type of every column was reviewed before performing calculations or joins.

- Identifiers such as `order_id`, `user_id`, and `product_id` were treated as integers.
- Descriptive fields such as `product_name`, `aisle`, and `department` were treated as strings.
- `days_since_prior_order` was stored as a float because it contains missing values.
- `reordered` was treated as a binary integer containing 0 or 1.

### Rationale

Correct data types are necessary for accurate filtering, joining, grouping, and aggregation. Identifiers are used as keys, while numerical fields such as `days_since_prior_order` are used in calculations.

## Step 3: Check and Retain Meaningful Missing Values

Missing-value counts were checked for every column in all six source files. The main finding was that `days_since_prior_order` contained 206,209 missing values, matching the number of unique customers. Each missing value belonged to a customer's first order, for which no previous order existed.

These values were retained as actual missing values (`NaN`). They were not filled with the text `"NaN"`, zero, a mean, or a median.

| Value in `days_since_prior_order` | Meaning |
|---|---|
| `NaN` | First order; no previous order exists |
| `0` | The customer placed another order on the same day |
| `1`–`29` | Number of days since the previous order |
| `30` | 30 or more days since the previous order |

### Rationale

The `NaN` value has a valid business meaning. Replacing it with zero would incorrectly classify a first order as a same-day repeat order and would distort average order-gap calculations. No missing-value imputation was performed.

## Step 4: Check Duplicate Records and Key Uniqueness

Duplicate checks were performed at both the full-row and identifier levels. The following key rules were validated:

- `order_id` is unique in `orders.csv`.
- `product_id` is unique in `products.csv`.
- `aisle_id` is unique in `aisles.csv`.
- `department_id` is unique in `departments.csv`.
- The combination of `order_id` and `product_id` identifies a product within an order.

Repeated `user_id` values in `orders.csv` were retained because one customer can place many orders. Repeated `product_id` values in the order-product files were also retained because the same product can appear in many different orders.

### Rationale

Duplicate validation prevents accidental double-counting while preserving valid one-to-many relationships. A repeated customer or product identifier is not automatically a duplicate; its meaning depends on the grain of the table.

## Step 5: Validate Acceptable Value Ranges

Logical range checks were applied to fields with known valid boundaries.

| Column | Validation rule |
|---|---|
| `order_id`, `user_id`, `product_id` | Must be greater than zero |
| `order_number` | Must be at least 1 |
| `order_dow` | Must be between 0 and 6 |
| `order_hour_of_day` | Must be between 0 and 23 |
| `days_since_prior_order` | Must be between 0 and 30, or `NaN` for a first order |
| `eval_set` | Must be `prior`, `train`, or `test` |
| `add_to_cart_order` | Must be at least 1 |
| `reordered` | Must be either 0 or 1 |
| Product, aisle, and department names | Must not be blank |

No invalid records were identified under these logical validation rules.

### Rationale

Bounded-domain validation identifies impossible values more accurately than statistical outlier rules for coded fields. For example, `order_dow` is a code from 0 to 6 and `order_hour_of_day` must remain within the 24-hour clock.

## Step 6: Validate Relationships Between Files

Referential-integrity checks were performed using the source identifiers:

- Product `aisle_id` values were checked against `aisles.csv`.
- Product `department_id` values were checked against `departments.csv`.
- Product identifiers in the order-product files were checked against `products.csv`.
- Order identifiers in the order-product files were checked against `orders.csv`.

No orphan product-to-aisle or product-to-department relationships were identified.

### Rationale

Relationship checks ensure that transaction records can be connected to the correct descriptive information. Without these checks, products could lose their aisle or department names after the joins.

## Step 7: Examine Potential Outliers

Numerical distributions were reviewed using descriptive statistics, histograms, box plots, and the interquartile-range method.

| File | Field | IQR outlier rule | IQR-flagged records | Percentage |
|---|---|---|---:|---:|
| `orders.csv` | `order_number` | Above 50 | 216,870 | 6.34% |
| `order_products__prior.csv` | `add_to_cart_order` | Above 23 | 1,357,124 | 4.1842% |
| `order_products__train.csv` | `add_to_cart_order` | 26 or above | 50,853 | 3.6727% |

Many flagged records had high `add_to_cart_order` values, indicating products placed later in large baskets. The flagged `order_number` records represent customers with many previous orders. These observations were retained as potentially large but valid baskets and frequent customers, not as data errors. Customers with many orders and orders with large basket sizes were also retained as valid customer behaviour.

Identifiers and coded fields such as `product_id`, `order_dow`, and `order_hour_of_day` were not interpreted using IQR because their numerical size does not measure business magnitude.

### Rationale

A statistical outlier is not necessarily an error. Removing these records would eliminate genuine large baskets and highly active customers, which are important for basket-size, customer-segmentation, and cross-selling analysis.

## Step 8: Retain Valid Special and Extreme Values

The following values were deliberately retained:

- `NaN` in `days_since_prior_order` for first orders
- Zero-day order gaps representing orders placed on the same day
- A value of 30 representing 30 or more days between orders
- High `order_number` values representing frequent customers
- High `add_to_cart_order` values representing large baskets
- Large basket sizes and high customer-order frequencies

### Rationale

These values describe genuine customer behaviour. Automatically deleting or replacing them would introduce bias and reduce the usefulness of the data for customer and market-basket analysis.

## Step 9: Prior and Train Files Remain Separate at This Stage

`order_products__prior.csv` and `order_products__train.csv` share the same columns and the same grain—one product within one order:

```text
32,434,489 prior records
+ 1,384,617 train records
= 33,819,106 order-item records (combined total)
```

At this stage (raw ingestion and local cleaning, covered by `create_duckdb.py`, `validate_duckdb.py`, and `Data Cleaning.ipynb`), the two files are kept as **separate tables** (`raw.order_products_prior` and `raw.order_products_train`). They are validated separately, and no `pd.concat()` or `UNION ALL` step is performed here.

### Rationale

Keeping prior and train separate at the raw layer lets each file's validation results (uniqueness, referential integrity, eval-set consistency) be checked and reported independently. Combining them into a single order-item table—equivalent to a `UNION ALL`—is a staging/transformation step that happens later in the pipeline (e.g. in dbt or a downstream feature-engineering step), not during raw ingestion or this cleaning pass.

Product records for `test` orders were not provided in the source dataset. Test orders remain in `orders.csv`, but they are excluded from basket-size, product-level, and order-item calculations.

## Step 10: Perform Final Validation

After cleaning and staging, the following checks were repeated:

- Row counts
- Column names
- Data types
- Missing values
- Key uniqueness
- Valid value ranges
- Table relationships
- Combined prior-and-train row count

### Rationale

Final validation confirms that the cleaning and staging operations did not accidentally remove, duplicate, or alter valid records before feature engineering began.

## Cleaning Outcome

The cleaning process found that the Instacart source files were generally high quality. Therefore, the work focused on validation and preservation rather than unnecessary deletion or imputation.

- Meaningful missing values were retained as `NaN`.
- No missing-value imputation was performed.
- Valid statistical outliers were retained.
- Large baskets and frequent customers were not deleted.
- The six original source files remained unchanged.
- Prior and train order-product records were validated separately and remain as separate tables at this stage; combining them happens in a later transformation step.
- Features such as `time_band`, `basket_size`, `reordered_item_count`, `customer_reorder_rate`, and `customer_segment` were created later during feature engineering, not during raw-data cleaning.
