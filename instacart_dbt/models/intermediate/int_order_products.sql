select
    order_id,
    product_id,
    add_to_cart_order,
    reordered,
    'prior' as source_eval_set
from {{ ref('stg_order_products_prior') }}

union all

select
    order_id,
    product_id,
    add_to_cart_order,
    reordered,
    'train' as source_eval_set
from {{ ref('stg_order_products_train') }}