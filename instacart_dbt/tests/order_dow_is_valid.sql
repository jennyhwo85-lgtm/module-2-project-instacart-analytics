select *
from {{ ref('fact_order_items') }}
where order_dow < 0
   or order_dow > 6