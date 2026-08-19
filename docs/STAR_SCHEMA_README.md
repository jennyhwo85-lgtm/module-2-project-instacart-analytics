## 6. Star Schema Design

A simple star-schema-based design was selected to organise the Instacart data into analysis-ready fact and dimension tables. The model separates measurable business events from descriptive information, making the data easier to understand and query.

The Instacart data was transformed into a star-schema-based analytical model. Two fact tables were retained because order information and product-item information have different levels of detail:

- `fact_order` contains one row per order.
- `fact_order_item` contains one row per product within an order.
- `dim_user` provides the customer identifier for customer-level analysis.
- `dim_product` provides product, aisle and department details.
- `dim_order_slot` provides day-and-hour ordering information.

The model contains one-to-many relationships: one user can place many orders, one order slot can contain many orders, one order can contain many order items, and one product can appear in many order items. Separating descriptive attributes into dimension tables avoids repeating customer and product information in the large fact tables. It also supports efficient analysis of customer segments, basket sizes, ordering patterns, product demand and reorder behaviour.
