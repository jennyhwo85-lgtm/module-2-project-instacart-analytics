from util import db_connection

db = db_connection()

result = db.execute("""
    SELECT
        order_dow,
        COUNT(*) AS order_count
    FROM raw_orders
    GROUP BY order_dow
    ORDER BY order_dow
""").fetchdf()

print(result)

db.close()