select *
from {{ ref('fact_order_items') }}
where order_hour_of_day < 0
   or order_hour_of_day > 23