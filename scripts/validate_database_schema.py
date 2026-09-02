'''
you should see the following output when you run this script:
┌──────────────────────────┬────────────┐
│        table_name        │ table_type │
│         varchar          │  varchar   │
├──────────────────────────┼────────────┤
│ dim_aisles               │ BASE TABLE │
│ dim_departments          │ BASE TABLE │
│ dim_orders               │ BASE TABLE │
│ dim_products             │ BASE TABLE │
│ dim_users                │ BASE TABLE │
│ fact_order_items         │ BASE TABLE │
│ int_order_items_enriched │ VIEW       │
│ int_order_products       │ VIEW       │
│ my_first_dbt_model       │ BASE TABLE │
│ my_second_dbt_model      │ VIEW       │
│ raw_aisles               │ BASE TABLE │
│ raw_departments          │ BASE TABLE │
│ raw_order_products_prior │ BASE TABLE │
│ raw_order_products_train │ BASE TABLE │
│ raw_orders               │ BASE TABLE │
│ raw_products             │ BASE TABLE │
│ stg_aisles               │ VIEW       │
│ stg_departments          │ VIEW       │
│ stg_order_products_prior │ VIEW       │
│ stg_order_products_train │ VIEW       │
│ stg_orders               │ VIEW       │
│ stg_products             │ VIEW       │
├──────────────────────────┴────────────┤
│ 22 rows                     2 columns │
└───────────────────────────────────────┘
'''
from util import db_connection

db = db_connection()

print(db.sql("""
    select table_name, table_type
    from information_schema.tables
    where table_schema = 'main'
    order by table_name
"""))

print(db.sql("""
    select count(*) as item_rows,
           count(distinct order_id) as orders,
           count(distinct product_id) as products,
           avg(reordered) as reorder_rate
    from fact_order_items
"""))

db.close()