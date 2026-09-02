select *
from {{ ref('fact_order_items') }}
where add_to_cart_order < 1