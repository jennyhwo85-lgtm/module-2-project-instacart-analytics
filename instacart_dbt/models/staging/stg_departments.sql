select
    cast(department_id as integer) as department_id,
    cast(department as varchar) as department_name
from {{ source('raw', 'departments') }}