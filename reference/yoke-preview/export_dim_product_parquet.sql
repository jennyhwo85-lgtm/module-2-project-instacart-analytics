export data options (
  uri = 'gs://sincere-stock-505109-m1-instacart-parquet/instacart_analytics/dim_product/part-*.parquet',
  format = 'PARQUET',
  overwrite = true
) as
select *
from `sincere-stock-505109-m1.instacart_analytics.dim_product`;