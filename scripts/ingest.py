from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
WAREHOUSE_DIR = PROJECT_ROOT / "warehouse"
DATABASE_PATH = WAREHOUSE_DIR / "instacart.duckdb"

WAREHOUSE_DIR.mkdir(exist_ok=True)

FILES = {
    "aisles": "aisles.csv",
    "departments": "departments.csv",
    "products": "products.csv",
    "orders": "orders.csv",
    "order_products_prior": "order_products__prior.csv",
    "order_products_train": "order_products__train.csv",
}


def main():
    connection = duckdb.connect(str(DATABASE_PATH))

    for table_name, file_name in FILES.items():
        file_path = DATA_DIR / file_name

        if not file_path.exists():
            raise FileNotFoundError(f"Missing file: {file_path}")

        connection.execute(f"""
            CREATE OR REPLACE TABLE raw_{table_name} AS
            SELECT *
            FROM read_csv_auto(
                '{file_path.as_posix()}',
                header = true
            )
        """)

        row_count = connection.execute(
            f"SELECT COUNT(*) FROM raw_{table_name}"
        ).fetchone()[0]

        print(f"Loaded raw_{table_name}: {row_count:,} rows")

    connection.close()
    print(f"\nDuckDB database created at:\n{DATABASE_PATH}")


if __name__ == "__main__":
    main()