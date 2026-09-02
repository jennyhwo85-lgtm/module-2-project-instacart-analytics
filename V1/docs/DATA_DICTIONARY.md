# Data Dictionary

This data dictionary documents the six original Instacart CSV files before transformation and the analytical tables produced after data preparation, transformation, and feature engineering.

## 1. Raw Data Dictionary — Before Transformation

### `orders.csv`

| Column | Data type | Description |
|---|---|---|
| `order_id` | Integer | Unique identifier for each order. |
| `user_id` | Integer | Unique identifier for each customer. |
| `eval_set` | String | Indicates whether the order belongs to the `prior`, `train`, or `test` set. |
| `order_number` | Integer | Sequential order number for each customer, beginning with 1. |
| `order_dow` | Integer | Day-of-week indicator from 0 to 6. The source dataset does not provide weekday names. |
| `order_hour_of_day` | Integer | Hour when the order was placed, from 0 to 23. |
| `days_since_prior_order` | Float | Days since the customer's previous order. The first order is null because no previous order exists. A value of 30 represents 30 or more days. |

### `products.csv`

| Column | Data type | Description |
|---|---|---|
| `product_id` | Integer | Unique product identifier. |
| `product_name` | String | Product name. |
| `aisle_id` | Integer | Identifier of the aisle containing the product. |
| `department_id` | Integer | Identifier of the department containing the product. |

### `aisles.csv`

| Column | Data type | Description |
|---|---|---|
| `aisle_id` | Integer | Unique aisle identifier. |
| `aisle` | String | Aisle name. |

### `departments.csv`

| Column | Data type | Description |
|---|---|---|
| `department_id` | Integer | Unique department identifier. |
| `department` | String | Department name. |

### `order_products__prior.csv`

| Column | Data type | Description |
|---|---|---|
| `order_id` | Integer | Identifier of the order. |
| `product_id` | Integer | Identifier of the product included in the order. |
| `add_to_cart_order` | Integer | Sequence in which the product was added to the basket. A value of 1 means the product was added first. |
| `reordered` | Integer (0/1) | Binary indicator where 1 means the customer had purchased the product previously and 0 means the product had not been purchased previously. |

### `order_products__train.csv`

| Column | Data type | Description |
|---|---|---|
| `order_id` | Integer | Identifier of the order. |
| `product_id` | Integer | Identifier of the product included in the order. |
| `add_to_cart_order` | Integer | Sequence in which the product was added to the basket. A value of 1 means the product was added first. |
| `reordered` | Integer (0/1) | Binary indicator where 1 means the customer had purchased the product previously and 0 means the product had not been purchased previously. |

The prior and train order-product files have the same grain and columns. They are combined using a `UNION ALL`-equivalent operation to create a complete order-item staging table without removing valid records. Product details for `test` orders are not provided and are therefore excluded from order-item analysis.

## 2. Analytical Model — After Transformation

The analytical model contains two fact tables at different grains and three supporting dimensions.

| Relationship | Cardinality |
|---|---|
| `dim_user` to `fact_order` | One customer to many orders |
| `dim_order_slot` to `fact_order` | One day-hour slot to many orders |
| `fact_order` to `fact_order_item` | One order to many order-item records |
| `dim_product` to `fact_order_item` | One product to many order-item records |

### `dim_product`

**Grain:** One row per product.

| Column | Data type | Key | Source or derivation | Description |
|---|---|---|---|---|
| `product_id` | Integer | Primary key | `products.csv` | Unique product identifier. |
| `product_name` | String | — | `products.csv` | Product name. |
| `aisle_id` | Integer | — | `products.csv` | Aisle identifier. |
| `aisle` | String | — | Joined from `aisles.csv` | Aisle name. |
| `department_id` | Integer | — | `products.csv` | Department identifier. |
| `department` | String | — | Joined from `departments.csv` | Department name. |

`dim_product` combines product, aisle, and department information so that product records can be analysed using readable category names without repeatedly joining three raw tables.

### `fact_order`

**Grain:** One row per order.

| Column | Data type | Key | Source or derivation | Description |
|---|---|---|---|---|
| `order_id` | Integer | Primary key | `orders.csv` | Unique order identifier. |
| `user_id` | Integer | Foreign key | `orders.csv` | References `dim_user.user_id`. |
| `slot_key` | String | Foreign key | Derived from `order_dow` and `order_hour_of_day` | References `dim_order_slot.slot_key`. |
| `order_number` | Integer | — | `orders.csv` | Sequential order number for the customer. |
| `order_dow` | Integer | — | `orders.csv` | Day-of-week indicator from 0 to 6. |
| `order_hour_of_day` | Integer | — | `orders.csv` | Hour when the order was placed, from 0 to 23. |
| `days_since_prior_order` | Float | — | `orders.csv` | Days since the customer's previous order; null for the first order. |

### `fact_order_item`

**Grain:** One product within one order.

| Column | Data type | Key | Source or derivation | Description |
|---|---|---|---|---|
| `order_id` | Integer | Composite key; foreign key | Combined prior and train order-product files | References `fact_order.order_id`. |
| `product_id` | Integer | Composite key; foreign key | Combined prior and train order-product files | References `dim_product.product_id`. |
| `add_to_cart_order` | Integer | — | Combined prior and train order-product files | Position in which the product was added to the basket. |
| `reordered` | Integer (0/1) | — | Combined prior and train order-product files | Indicates whether the customer had purchased the product previously. |

The combination of `order_id` and `product_id` identifies an order-item record. Each row represents a product occurrence in an order, not a product quantity or monetary sale.

### `dim_order_slot`

**Grain:** One day-and-hour combination, giving 168 possible combinations (`7 × 24`).

| Column | Data type | Key | Source or derivation | Description |
|---|---|---|---|---|
| `slot_key` | String | Primary key | Combination of `order_dow` and `order_hour_of_day`, such as `0_10` | Unique day-and-hour identifier. |
| `order_dow` | Integer | — | `orders.csv` | Day-of-week indicator from 0 to 6. |
| `order_hour_of_day` | Integer | — | `orders.csv` | Hour of day from 0 to 23. |
| `time_band` | String | — | Derived from `order_hour_of_day` | Broader shopping period: Night, Morning, Afternoon, or Evening. |

The time bands are defined as follows:

| Time band | Included hours |
|---|---|
| Night | 00:00–05:59 |
| Morning | 06:00–11:59 |
| Afternoon | 12:00–17:59 |
| Evening | 18:00–23:59 |

### `dim_user`

**Grain:** One row per customer.

Customer-level features are engineered so that customer behaviour can be analysed without repeatedly aggregating millions of order and order-item records.

| Column | Data type | Key | Source or derivation | Description |
|---|---|---|---|---|
| `user_id` | Integer | Primary key | `orders.csv` | Unique customer identifier. |
| `total_orders` | Integer | — | Count of unique `order_id` values per customer | Measures customer order activity. |
| `average_days_between_orders` | Float | — | Mean `days_since_prior_order`, excluding the first-order null | Measures how frequently the customer returns. |
| `average_basket_size` | Float | — | Mean basket size per customer | Measures the customer's typical number of products per order. |
| `total_items` | Integer | — | Sum of basket sizes per customer | Total number of order-product records associated with the customer. |
| `total_reordered_items` | Integer | — | Sum of reordered product records per customer | Total number of repeat-purchase records associated with the customer. |
| `unique_products_purchased` | Integer | — | Count of distinct `product_id` values per customer | Measures the variety of products purchased. |
| `customer_reorder_rate` | Float | — | `total_reordered_items ÷ total_items` | Decimal measure of repeat-purchase behaviour, ranging from 0 to 1. |
| `customer_reorder_percentage` | Float | — | `customer_reorder_rate × 100` | Business-friendly percentage measure of repeat-purchase behaviour. |
| `customer_segment` | String | — | Median-based rule using `total_orders` and `customer_reorder_rate` | Assigns the customer to one behavioural segment. |

The order-gap calculation excludes the first-order null because a customer's first order has no previous order. Basket, product-variety, and reorder features use prior and train order-product records because test-order product details are unavailable.

## 3. Customer-Segment Rules

Customer segments are assigned using two engineered variables:

- **Order activity:** whether `total_orders` is at or above the dataset median.
- **Repeat-purchase tendency:** whether `customer_reorder_rate` is at or above the dataset median.

| Order activity | Reorder rate | Customer segment | Interpretation |
|---|---|---|---|
| At or above median | At or above median | Frequent Repeat Customers | Places orders frequently and regularly repurchases familiar products. |
| At or above median | Below median | Frequent Variety Customers | Places orders frequently but has a lower tendency to repurchase familiar products. |
| Below median | At or above median | Occasional Repeat Customers | Places orders less frequently but regularly repurchases familiar products. |
| Below median | Below median | Occasional Variety Customers | Places orders less frequently and has a lower tendency to repurchase familiar products. |

For the analysed dataset, the median thresholds are approximately 10 orders and a 44.3% customer reorder rate. The thresholds are calculated from the data rather than being arbitrary business cut-offs.

In these labels, **Variety** means a lower reorder tendency relative to the dataset median. It does not directly mean that the customer purchased more unique products. `average_basket_size`, `unique_products_purchased`, and `average_days_between_orders` are used to describe and compare the resulting segments, but they do not determine the segment assignment.

## 4. Derived Analytical Metrics

| Metric | Calculation | Purpose |
|---|---|---|
| `basket_size` | Number of order-product records per `order_id` | Measures the number of products in an order. |
| `reordered_item_count` | Sum of `reordered` per `order_id` | Counts previously purchased products in an order. |
| `average_basket_size` | Mean basket size for the selected orders or customer | Measures typical order size. |
| `customer_reorder_rate` | Total reordered customer-product records ÷ total customer-product records | Measures customer repeat-purchase behaviour. |
| `customer_reorder_percentage` | `customer_reorder_rate × 100` | Presents the reorder rate in an easier-to-read business format. |
| `average_days_between_orders` | Mean `days_since_prior_order`, excluding the first-order null | Measures customer purchasing frequency. |
| `unique_products_purchased` | Number of distinct products purchased by a customer | Measures customer product variety. |
| `purchase_count` | Number of order-product records per product | Measures how frequently a product appears in orders. |
| `product_reorder_rate` | Reordered records for a product ÷ total purchase records for that product | Measures repeat demand for a product. |
| `first_added_count` | Count of product records where `add_to_cart_order = 1` | Identifies products frequently added first. |
| `first_added_rate` | First-added count for a product ÷ purchase count for that product | Measures how often a product starts a basket. |
| `slot_key` | Combination of day-of-week and hour | Connects orders to the order-time dimension. |
| `time_band` | Grouped order hour | Simplifies comparisons across periods of the day. |

## 5. Interpretation and Scope Notes

- The dataset does not contain product quantity, price, revenue, or calendar-date fields. Therefore, `purchase_count` represents product occurrences in orders rather than units sold or sales revenue.
- Valid large baskets and highly active customers are retained because they represent meaningful purchasing behaviour rather than automatic data errors.
- Missing `days_since_prior_order` values for first orders are retained because the missing value has a valid business meaning.
- `order_dow` is retained as values 0–6. Weekday names should not be assigned unless a mapping is explicitly defined for the analysis.
- Product-level reorder and first-added rates should be interpreted together with `purchase_count` because rates based on very few purchases can be unstable.

## 6. Open Items Pending Confirmation with Warehouse Owner (Lai Yoke)

The ERD shared on 2026-08-19 does not yet match this dictionary in a few places. Tracked here until resolved:

- `dim_user` in the ERD currently only has `user_key` + `user_id`; the ten engineered features listed in Section 2 above (`total_orders`, `average_basket_size`, `customer_reorder_rate`, `customer_segment`, etc.) still need to be added to `dim_user` or split into a separate features table.
- `slot_key` data type: this document defines it as a string (e.g. `"0_10"`); the ERD currently shows `int`.
- Naming: this document uses `time_band`; the ERD currently uses `day_part`.
- `reordered` data type: this document defines it as integer (0/1), matching the raw source; the ERD currently shows `boolean`.
- `fact_order_item.item_count`: appears in the ERD but is not defined anywhere in this dictionary. Needs a definition, since the source data has no purchase-quantity field.
- `fact_order.basket_size`, `reordered_item_count`, `reorder_rate`: assumed to be pre-computed and materialized during the ELT stage rather than calculated on the fly — pending confirmation.
