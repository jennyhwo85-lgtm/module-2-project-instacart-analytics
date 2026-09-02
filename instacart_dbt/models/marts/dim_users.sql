select
    user_id,
    count(distinct order_id) as observed_order_count,
    count(*) as observed_item_count,
    sum(reordered) as reordered_item_count,
    cast(sum(reordered) as double) / nullif(count(*), 0) as reorder_rate
from {{ ref('int_order_items_enriched') }}
group by user_id