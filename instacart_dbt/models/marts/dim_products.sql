select
    product_id,
    product_name,
    aisle_id,
    department_id
from {{ ref('stg_products') }}