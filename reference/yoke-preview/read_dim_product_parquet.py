from pathlib import Path

import pyarrow.compute as pc
import pyarrow.dataset as ds


PARQUET_DIRECTORY = Path("Parquet/dim_product")
EXPECTED_ROWS = 49_688


# Decode and read the Parquet dataset.
dataset = ds.dataset(PARQUET_DIRECTORY, format="parquet")
table = dataset.to_table()

row_count = table.num_rows
unique_products = pc.count_distinct(table["product_id"]).as_py()
missing_product_ids = table["product_id"].null_count

print("PyArrow successfully decoded the Parquet file.")
print(f"Rows: {row_count:,}")
print(f"Columns: {table.num_columns}")
print(f"Unique product IDs: {unique_products:,}")
print(f"Missing product IDs: {missing_product_ids}")

print("\nSchema:")
print(table.schema)

print("\nFirst five rows:")
for row in table.slice(0, 5).to_pylist():
    print(row)

if row_count != EXPECTED_ROWS:
    raise ValueError(
        f"Row-count mismatch: expected {EXPECTED_ROWS:,}, found {row_count:,}"
    )

if unique_products != EXPECTED_ROWS:
    raise ValueError("The product_id column is not unique.")

if missing_product_ids != 0:
    raise ValueError("The product_id column contains missing values.")

print("\nValidation passed: the Parquet data matches dim_product.")