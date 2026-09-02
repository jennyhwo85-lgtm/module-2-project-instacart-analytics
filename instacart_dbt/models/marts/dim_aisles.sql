select
    aisle_id,
    aisle_name
from {{ ref('stg_aisles') }}