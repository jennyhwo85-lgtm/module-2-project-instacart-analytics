from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "Warehouse" / "instacart.duckdb"
OUTPUT_DIRECTORY = PROJECT_ROOT / "supabase_import"

MAX_USER_ID = 20_000


EXPORTS = {
    "aisles.csv": """
        SELECT
            aisle_id,
            aisle
        FROM raw.aisles
    """,
    "departments.csv": """
        SELECT
            department_id,
            department
        FROM raw.departments
    """,
    "products.csv": """
        SELECT
            product_id,
            product_name,
            aisle_id,
            department_id
        FROM raw.products
    """,
    "orders.csv": f"""
        SELECT
            order_id,
            user_id,
            eval_set,
            order_number,
            order_dow,
            order_hour_of_day,
            days_since_prior_order
        FROM raw.orders
        WHERE user_id <= {MAX_USER_ID}
    """,
    "order_products__prior.csv": f"""
        SELECT
            op.order_id,
            op.product_id,
            op.add_to_cart_order,
            op.reordered
        FROM raw.order_products_prior AS op
        INNER JOIN raw.orders AS orders
            ON orders.order_id = op.order_id
        WHERE orders.user_id <= {MAX_USER_ID}
    """,
    "order_products__train.csv": f"""
        SELECT
            op.order_id,
            op.product_id,
            op.add_to_cart_order,
            op.reordered
        FROM raw.order_products_train AS op
        INNER JOIN raw.orders AS orders
            ON orders.order_id = op.order_id
        WHERE orders.user_id <= {MAX_USER_ID}
    """,
}


def export_csv(
    connection: duckdb.DuckDBPyConnection,
    filename: str,
    query: str,
) -> None:
    output_path = OUTPUT_DIRECTORY / filename
    escaped_path = str(output_path).replace("'", "''")

    connection.execute(
        f"""
        COPY ({query})
        TO '{escaped_path}'
        (HEADER, DELIMITER ',')
        """
    )

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"Exported {filename}: {size_mb:,.1f} MB")


def main() -> None:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(f"DuckDB database not found: {DATABASE_PATH}")

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)

    connection = duckdb.connect(str(DATABASE_PATH), read_only=True)

    try:
        for filename, query in EXPORTS.items():
            export_csv(connection, filename, query)
    finally:
        connection.close()

    total_size = sum(
        file_path.stat().st_size
        for file_path in OUTPUT_DIRECTORY.glob("*.csv")
    )

    print()
    print("Supabase subset export completed.")
    print(f"Selected users: user_id <= {MAX_USER_ID:,}")
    print(f"Total CSV size: {total_size / (1024 * 1024):,.1f} MB")
    print(f"Output directory: {OUTPUT_DIRECTORY}")


if __name__ == "__main__":
    main()