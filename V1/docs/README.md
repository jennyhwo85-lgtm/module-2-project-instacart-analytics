# Instacart Market Basket Analysis — Full Project Write-up

> This is the detailed project write-up (business problem, objectives, assignment mapping, data cleaning summary, and feature engineering). The root [`README.md`](../README.md) is the short entry point; this document has the full detail.

## 1. Business Problem

Instacart processes millions of customer orders across thousands of products. However, the original data is distributed across six separate CSV files, making it difficult for business users to analyse ordering patterns, customer behaviour and product demand efficiently.

Without an organised analytical data model, Instacart may find it difficult to answer important questions such as when customers place orders, what a typical order contains, which products are purchased and reordered most frequently, and how customers differ in their purchasing behaviour.

This project develops a data pipeline, analytical data warehouse and interactive dashboard that transform the raw Instacart data into structured and reusable business information. The resulting insights can support workforce planning, product availability, customer engagement and repeat-order recommendations.

## 2. Project Objectives

The objectives of this project are to:

1. Ingest the six Instacart source files into BigQuery to provide centralised and scalable data storage.
2. Clean and validate the raw data by checking missing values, duplicate records, data types and logical inconsistencies.
3. Transform the source data into a star-schema-based analytical model containing customer, product, order-time, order and order-item tables.
4. Engineer customer, order and product features such as basket size, customer order frequency, reorder rate, average order gap and customer segment.
5. Use Python and pandas to analyse ordering patterns, customer purchasing behaviour and product demand.
6. Develop a Streamlit dashboard that communicates the findings through KPI cards, charts, filters and business implications.

## 3. Fulfilment of the Assignment Questions

The assignment recommends analysing monthly sales trends, top-selling products and customer segmentation by purchasing behaviour. These requirements were adapted to the information available in the Instacart dataset. Full original brief: [`assignment_brief.md`](assignment_brief.md).

| Assignment question | Implementation in this project | Rationale |
|---|---|---|
| Monthly sales trends | Order activity by day of week and hour of day | The dataset does not contain calendar dates or months. Day-and-hour ordering patterns were therefore used as the most appropriate time-based analysis. |
| Top-selling products | Most frequently purchased products and products with high reorder rates | Product prices, revenue and item quantities are unavailable. Product demand is therefore measured using the number of order-product records rather than sales value. |
| Customer segmentation by purchase behaviour | Frequent Repeat Customers, Frequent Variety Customers and Occasional Repeat Customers | Customers were grouped using engineered behavioural features, including order frequency, product variety, basket size, reorder rate and average order gap. |

The dataset-specific business questions correspond directly to the three dashboard pages:

| Dashboard page | What the dashboard analyses | Business question |
|---|---|---|
| **1. Overview / Order Activity** | Overall KPIs, peak day, peak hour, peak time slot, most common basket size, day-and-hour ordering patterns and basket-size distribution | **When do customers place orders, and what is the typical number of products in each order?** |
| **2. Customer Segments** | Frequent Repeat Customers, Frequent Variety Customers and Occasional Repeat Customers, including order frequency, product variety, basket size, reorder rate and average order gap | **What customer purchasing segments exist, and how do their ordering, basket-size, product-variety and reordering behaviours differ?** |
| **3. Product Analysis** | Top purchased products, product reorder rates, department and aisle demand, and products most frequently added first (`add_to_cart_order = 1`) | **Which products are purchased most frequently, which have high reorder rates, and which products are most frequently added first to customers' baskets? Which departments and aisles account for the highest product demand?** |

The term *most frequently purchased* is used instead of *top-selling* because the dataset does not provide prices, revenue or quantities.

## 4. Data Cleaning and Validation (Summary)

Each of the six source files was profiled separately before the tables were joined. The profiling process examined the number of rows and columns, column names, data types, missing values, exact duplicate rows, duplicate business keys and logical validity. Meaningful missing values were retained instead of being automatically replaced or deleted.

Full step-by-step process: [`DATA_CLEANING_README.md`](DATA_CLEANING_README.md).

### Data-type validation

Column data types were inspected to ensure that identifiers and numerical fields were represented correctly. Fields such as `order_id`, `user_id`, `product_id`, `order_number`, `order_dow`, `order_hour_of_day`, `add_to_cart_order` and `reordered` were validated as numerical fields. This prevents failed joins and incorrect calculations.

### Missing-value validation

Missing values were evaluated according to their business meaning. In `orders.csv`, `days_since_prior_order` is missing for each customer's first order because no previous order exists. These values were retained as null rather than replaced with zero. A zero value would mean that the customer placed another order on the same day, which is different from having no previous order.

### Duplicate validation

Exact duplicate rows and duplicate business keys were checked separately. The main uniqueness checks covered `order_id`, `product_id`, `user_id` and the combined `order_id`–`product_id` key in the order-item data. This prevents the same business event from being counted more than once.

### Logical validation

The following business rules were checked:

- `order_dow` must be between 0 and 6.
- `order_hour_of_day` must be between 0 and 23.
- `order_number` must be at least 1.
- `add_to_cart_order` must be at least 1.
- `reordered` must contain only 0 or 1.
- Product IDs in the order-item table must exist in the product dimension.
- Order IDs in the order-item table must exist in the order fact table.

### Data integration

The prior and training order-product files were combined to create a unified order-item fact table. Product records were enriched by joining `products.csv`, `aisles.csv` and `departments.csv` through their corresponding identifiers. Customer features were created by connecting order and order-item records through `order_id` and aggregating the results by `user_id`.

## 5. Feature Engineering

Feature engineering transformed the cleaned transaction-level records into business-friendly variables that could be reused in customer, order and product analysis. The features were calculated before dashboard visualisation so that the metric definitions remained consistent and the dashboard could use prepared analytical summaries.

| Engineered feature | Calculation | Analytical purpose |
|---|---|---|
| Total customer orders | Number of unique orders for each user | Measures customer purchasing frequency |
| Basket size | Number of product records associated with each order | Measures order size and operational workload |
| Average basket size | Average basket size for each customer | Compares customer purchasing volume |
| Customer reorder rate | Reordered product records divided by total product records for each customer | Measures repeat-purchase behaviour |
| Average order gap | Mean `days_since_prior_order`, excluding first-order nulls | Measures how frequently customers return |
| Unique products | Number of distinct products purchased by each customer | Measures product variety |
| Customer segment | Rule-based combination of order frequency, repeat purchasing and product variety | Creates interpretable customer groups |
| Slot key | Combination of day of week and hour of day | Supports order-time analysis |
| Time band | Order hour grouped into periods of the day | Simplifies time-based comparisons |
| Product purchase count | Number of order-product records for each product | Measures product demand |
| Product reorder rate | Reordered records divided by product purchase records | Identifies products with repeat demand |

### Basket size

Basket size was calculated by counting the product records associated with each `order_id`. The overall average basket size was 10.11 products across orders with available item-level information. Test orders were excluded because their product contents were not provided.

```text
33,819,106 order-product records ÷ 3,346,083 orders with item data = 10.11 products
```

This feature estimates the average picking, packing and delivery workload for each order. The basket-size distribution was also examined because a smaller number of large baskets can raise the overall average.

### Customer features and segmentation

Customer-level features were stored in `dim_user` at one row per customer. This avoids repeatedly aggregating millions of order and order-item records whenever customer behaviour is analysed. It also ensures that the analysis and dashboard use consistent customer definitions.

The customer segmentation is rule-based and uses the behavioural features created during feature engineering:

- **Frequent Repeat Customers** order frequently and show stronger repeat-purchase behaviour.
- **Frequent Variety Customers** order frequently while purchasing a wider variety of products.
- **Occasional Repeat Customers** order less frequently but continue to repurchase some familiar products.

### Product and time features

Product purchase counts and reorder rates were calculated to identify products with high overall demand and repeat demand. The `slot_key` and time-band features were derived from `order_dow` and `order_hour_of_day` to support analysis of ordering activity across different days and times.

Overall, the engineered features convert technical transaction-level fields into metrics that business users can understand. For example, the raw `reordered` indicator becomes a customer or product reorder rate, while individual order-product records become basket-size and product-demand measures.

Full field-level definitions of all engineered features: [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md) §2 and §4.
