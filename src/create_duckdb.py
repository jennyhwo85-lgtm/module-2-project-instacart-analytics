from pathlib import Path
import time

import duckdb


# Locate folders relative to this script.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = PROJECT_ROOT / "Dataset"
WAREHOUSE_DIR = PROJECT_ROOT / "Warehouse"
DATABASE_PATH = WAREHOUSE_DIR / "instacart.duckdb"


# Only the six original source files belong in the raw layer.
TABLES = {
    "aisles": {
        "filename": "aisles.csv",
        "columns": """
            CAST(aisle_id AS INTEGER) AS aisle_id,
            CAST(aisle AS VARCHAR) AS aisle
        """,
        "expected_rows": 134,
    },
    "departments": {
        "filename": "departments.csv",
        "columns": """
            CAST(department_id AS INTEGER) AS department_id,
            CAST(department AS VARCHAR) AS department
        """,
        "expected_rows": 21,
    },
    "products": {
        "filename": "products.csv",
        "columns": """
            CAST(product_id AS INTEGER) AS product_id,
            CAST(product_name AS VARCHAR) AS product_name,
            CAST(aisle_id AS INTEGER) AS aisle_id,
            CAST(department_id AS INTEGER) AS department_id
        """,
        "expected_rows": 49688,
    },
    "orders": {
        "filename": "orders.csv",
        "columns": """
            CAST(order_id AS INTEGER) AS order_id,
            CAST(user_id AS INTEGER) AS user_id,
            CAST(eval_set AS VARCHAR) AS eval_set,
            CAST(order_number AS INTEGER) AS order_number,
            CAST(order_dow AS INTEGER) AS order_dow,
            CAST(order_hour_of_day AS INTEGER) AS order_hour_of_day,
            CAST(days_since_prior_order AS DOUBLE)
                AS days_since_prior_order
        """,
        "expected_rows": 3421083,
    },
    "order_products_prior": {
        "filename": "order_products__prior.csv",
        "columns": """
            CAST(order_id AS INTEGER) AS order_id,
            CAST(product_id AS INTEGER) AS product_id,
            CAST(add_to_cart_order AS INTEGER)
                AS add_to_cart_order,
            CAST(reordered AS INTEGER) AS reordered
        """,
        "expected_rows": 32434489,
    },
    "order_products_train": {
        "filename": "order_products__train.csv",
        "columns": """
            CAST(order_id AS INTEGER) AS order_id,
            CAST(product_id AS INTEGER) AS product_id,
            CAST(add_to_cart_order AS INTEGER)
                AS add_to_cart_order,
            CAST(reordered AS INTEGER) AS reordered
        """,
        "expected_rows": 1384617,
    },
}


def check_source_files():
    """Stop immediately if any required source file is missing."""
    missing_files = []

    for specification in TABLES.values():
        file_path = DATASET_DIR / specification["filename"]

        if not file_path.exists():
            missing_files.append(str(file_path))

    if missing_files:
        missing_text = "\n".join(missing_files)
        raise FileNotFoundError(
            f"Required source files are missing:\n{missing_text}"
        )


def create_raw_tables():
    """Load the original CSV files into DuckDB raw tables."""
    check_source_files()
    WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)

    connection = duckdb.connect(str(DATABASE_PATH))

    try:
        connection.execute("CREATE SCHEMA IF NOT EXISTS raw")

        for table_name, specification in TABLES.items():
            start_time = time.perf_counter()

            csv_path = (
                DATASET_DIR / specification["filename"]
            ).as_posix()

            print(f"Loading raw.{table_name}...")

            connection.execute(
                f"""
                CREATE OR REPLACE TABLE raw.{table_name} AS
                SELECT
                    {specification["columns"]}
                FROM read_csv_auto(
                    '{csv_path}',
                    header = true
                )
                """
            )

            actual_rows = connection.execute(
                f"SELECT COUNT(*) FROM raw.{table_name}"
            ).fetchone()[0]

            expected_rows = specification["expected_rows"]
            elapsed_time = time.perf_counter() - start_time

            if actual_rows != expected_rows:
                raise ValueError(
                    f"Row-count failure for raw.{table_name}: "
                    f"expected {expected_rows:,}, "
                    f"found {actual_rows:,}"
                )

            print(
                f"Completed raw.{table_name}: "
                f"{actual_rows:,} rows "
                f"({elapsed_time:.1f} seconds)"
            )

    finally:
        connection.close()

    database_size_mb = DATABASE_PATH.stat().st_size / (1024 ** 2)

    print("\nDuckDB ingestion completed successfully.")
    print(f"Database: {DATABASE_PATH}")
    print(f"Database size: {database_size_mb:,.1f} MB")


if __name__ == "__main__":
    create_raw_tables()