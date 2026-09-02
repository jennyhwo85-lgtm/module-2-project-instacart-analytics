select
    order_id,
    user_id,
    product_id,
    aisle_id,
    department_id,
    eval_set,
    order_number,
    order_dow,
    order_hour_of_day,
    days_since_prior_order,
    add_to_cart_order,
    reordered,
    source_eval_set
from {{ ref('int_order_items_enriched') }}