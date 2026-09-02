select
    cast(aisle_id as integer) as aisle_id,
    cast(aisle as varchar) as aisle_name
from {{ source('raw', 'aisles') }}