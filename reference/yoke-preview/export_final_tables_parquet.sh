#!/usr/bin/env bash

set -euo pipefail

PROJECT_ID="sincere-stock-505109-m1"
DATASET="instacart_analytics"
BUCKET="sincere-stock-505109-m1-instacart-parquet"
LOCATION="asia-southeast1"

TABLES=(
  "dim_product"
  "dim_order_slot"
  "dim_user"
  "fact_order"
  "fact_order_item"
)

for table in "${TABLES[@]}"; do
  destination="gs://${BUCKET}/${DATASET}/${table}/part-*.parquet"

  if gcloud storage ls "${destination}" >/dev/null 2>&1; then
    echo "SKIP ${table}: Parquet files already exist."
    continue
  fi

  echo "Exporting ${table}..."

  bq extract \
    --location="${LOCATION}" \
    --destination_format=PARQUET \
    "${PROJECT_ID}:${DATASET}.${table}" \
    "${destination}"
done

echo "Parquet export check completed."