'''
your should see the following output when you run this script:
missing orders : 0
missing products : 0
invalid reordered values : 0
'''

from util import db_connection

db = db_connection()

checks = {
    "missing orders": """
        select count(*)
        from fact_order_items f
        left join dim_orders o on f.order_id = o.order_id
        where o.order_id is null
    """,
    "missing products": """
        select count(*)
        from fact_order_items f
        left join dim_products p on f.product_id = p.product_id
        where p.product_id is null
    """,
    "invalid reordered values": """
        select count(*)
        from fact_order_items
        where reordered not in (0, 1)
    """
}

for name, query in checks.items():
    print(name, ":", db.sql(query).fetchone()[0])

db.close()