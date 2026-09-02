select
    cast(order_id as integer) as order_id,
    cast(product_id as integer) as product_id,
    cast(add_to_cart_order as integer) as add_to_cart_order,
    cast(reordered as integer) as reordered,
    'train' as source_eval_set
from {{ source('raw', 'order_products_train') }}