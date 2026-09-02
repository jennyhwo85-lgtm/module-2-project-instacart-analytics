select *
from {{ ref('fact_order_items') }}
where source_eval_set not in ('prior', 'train')