from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "Warehouse" / "instacart.duckdb"


# These contracts match the DuckDB creation script and the six datasets
# inspected in the Data Cleaning notebook.
EXPECTED_TABLES = {
    "aisles": {
        "row_count": 134,
        "columns": {
            "aisle_id": "INTEGER",
            "aisle": "VARCHAR",
        },
    },
    "departments": {
        "row_count": 21,
        "columns": {
            "department_id": "INTEGER",
            "department": "VARCHAR",
        },
    },
    "products": {
        "row_count": 49688,
        "columns": {
            "product_id": "INTEGER",
            "product_name": "VARCHAR",
            "aisle_id": "INTEGER",
            "department_id": "INTEGER",
        },
    },
    "orders": {
        "row_count": 3421083,
        "columns": {
            "order_id": "INTEGER",
            "user_id": "INTEGER",
            "eval_set": "VARCHAR",
            "order_number": "INTEGER",
            "order_dow": "INTEGER",
            "order_hour_of_day": "INTEGER",
            "days_since_prior_order": "DOUBLE",
        },
    },
    "order_products_prior": {
        "row_count": 32434489,
        "columns": {
            "order_id": "INTEGER",
            "product_id": "INTEGER",
            "add_to_cart_order": "INTEGER",
            "reordered": "INTEGER",
        },
    },
    "order_products_train": {
        "row_count": 1384617,
        "columns": {
            "order_id": "INTEGER",
            "product_id": "INTEGER",
            "add_to_cart_order": "INTEGER",
            "reordered": "INTEGER",
        },
    },
}


TESTS = [
    (
        "Dimension and order primary keys are unique",
        """
        SELECT
            (SELECT COUNT(*) - COUNT(DISTINCT aisle_id)
             FROM raw.aisles)
          + (SELECT COUNT(*) - COUNT(DISTINCT department_id)
             FROM raw.departments)
          + (SELECT COUNT(*) - COUNT(DISTINCT product_id)
             FROM raw.products)
          + (SELECT COUNT(*) - COUNT(DISTINCT order_id)
             FROM raw.orders)
        """,
    ),
    (
        "Prior order-product combinations are unique",
        """
        SELECT COUNT(*)
        FROM (
            SELECT order_id, product_id
            FROM raw.order_products_prior
            GROUP BY order_id, product_id
            HAVING COUNT(*) > 1
        )
        """,
    ),
    (
        "Train order-product combinations are unique",
        """
        SELECT COUNT(*)
        FROM (
            SELECT order_id, product_id
            FROM raw.order_products_train
            GROUP BY order_id, product_id
            HAVING COUNT(*) > 1
        )
        """,
    ),
    (
        "Required fields contain no nulls",
        """
        SELECT
            (SELECT COUNT(*) FROM raw.aisles
             WHERE aisle_id IS NULL OR aisle IS NULL)
          + (SELECT COUNT(*) FROM raw.departments
             WHERE department_id IS NULL
                OR department IS NULL)
          + (SELECT COUNT(*) FROM raw.products
             WHERE product_id IS NULL
                OR product_name IS NULL
                OR aisle_id IS NULL
                OR department_id IS NULL)
          + (SELECT COUNT(*) FROM raw.orders
             WHERE order_id IS NULL
                OR user_id IS NULL
                OR eval_set IS NULL
                OR order_number IS NULL
                OR order_dow IS NULL
                OR order_hour_of_day IS NULL)
          + (SELECT COUNT(*)
             FROM raw.order_products_prior
             WHERE order_id IS NULL
                OR product_id IS NULL
                OR add_to_cart_order IS NULL
                OR reordered IS NULL)
          + (SELECT COUNT(*)
             FROM raw.order_products_train
             WHERE order_id IS NULL
                OR product_id IS NULL
                OR add_to_cart_order IS NULL
                OR reordered IS NULL)
        """,
    ),
    (
        "Required text fields are not blank",
        """
        SELECT
            (SELECT COUNT(*) FROM raw.aisles
             WHERE TRIM(aisle) = '')
          + (SELECT COUNT(*) FROM raw.departments
             WHERE TRIM(department) = '')
          + (SELECT COUNT(*) FROM raw.products
             WHERE TRIM(product_name) = '')
          + (SELECT COUNT(*) FROM raw.orders
             WHERE TRIM(eval_set) = '')
        """,
    ),
    (
        "Products reference valid aisles and departments",
        """
        SELECT COUNT(*)
        FROM raw.products AS p
        LEFT JOIN raw.aisles AS a
            ON p.aisle_id = a.aisle_id
        LEFT JOIN raw.departments AS d
            ON p.department_id = d.department_id
        WHERE a.aisle_id IS NULL
           OR d.department_id IS NULL
        """,
    ),
    (
        "Prior items reference valid orders",
        """
        SELECT COUNT(*)
        FROM raw.order_products_prior AS op
        LEFT JOIN raw.orders AS o
            ON op.order_id = o.order_id
        WHERE o.order_id IS NULL
        """,
    ),
    (
        "Prior items reference valid products",
        """
        SELECT COUNT(*)
        FROM raw.order_products_prior AS op
        LEFT JOIN raw.products AS p
            ON op.product_id = p.product_id
        WHERE p.product_id IS NULL
        """,
    ),
    (
        "Train items reference valid orders and products",
        """
        SELECT COUNT(*)
        FROM raw.order_products_train AS op
        LEFT JOIN raw.orders AS o
            ON op.order_id = o.order_id
        LEFT JOIN raw.products AS p
            ON op.product_id = p.product_id
        WHERE o.order_id IS NULL
           OR p.product_id IS NULL
        """,
    ),
    (
        "Order values follow logical ranges",
        """
        SELECT COUNT(*)
        FROM raw.orders
        WHERE order_number < 1
           OR order_dow NOT BETWEEN 0 AND 6
           OR order_hour_of_day NOT BETWEEN 0 AND 23
           OR eval_set NOT IN ('prior', 'train', 'test')
           OR (
               order_number = 1
               AND days_since_prior_order IS NOT NULL
           )
           OR (
               order_number > 1
               AND days_since_prior_order IS NULL
           )
           OR (
               days_since_prior_order IS NOT NULL
               AND days_since_prior_order NOT BETWEEN 0 AND 30
           )
        """,
    ),
    (
        "Prior item values follow logical ranges",
        """
        SELECT COUNT(*)
        FROM raw.order_products_prior
        WHERE add_to_cart_order < 1
           OR reordered NOT IN (0, 1)
        """,
    ),
    (
        "Train item values follow logical ranges",
        """
        SELECT COUNT(*)
        FROM raw.order_products_train
        WHERE add_to_cart_order < 1
           OR reordered NOT IN (0, 1)
        """,
    ),
    (
        "Prior items belong only to prior orders",
        """
        SELECT COUNT(*)
        FROM raw.order_products_prior AS op
        INNER JOIN raw.orders AS o
            ON op.order_id = o.order_id
        WHERE o.eval_set <> 'prior'
        """,
    ),
    (
        "Train items belong only to train orders",
        """
        SELECT COUNT(*)
        FROM raw.order_products_train AS op
        INNER JOIN raw.orders AS o
            ON op.order_id = o.order_id
        WHERE o.eval_set <> 'train'
        """,
    ),
]


def check_table_structure(connection):
    """Confirm that the raw tables, columns, and types still match."""
    actual_tables = {
        row[0]
        for row in connection.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'raw'
              AND table_type = 'BASE TABLE'
            """
        ).fetchall()
    }

    expected_tables = set(EXPECTED_TABLES)
    missing_tables = expected_tables - actual_tables

    if missing_tables:
        missing_text = ", ".join(sorted(missing_tables))
        raise ValueError(
            f"Required DuckDB raw tables are missing: {missing_text}"
        )

    print("PASS: All six raw tables exist")

    for table_name, specification in EXPECTED_TABLES.items():
        table_description = connection.execute(
            f"DESCRIBE raw.{table_name}"
        ).fetchall()

        actual_columns = {
            row[0]: row[1].upper()
            for row in table_description
        }

        expected_columns = {
            column_name: column_type.upper()
            for column_name, column_type
            in specification["columns"].items()
        }

        if actual_columns != expected_columns:
            raise ValueError(
                f"Schema failure for raw.{table_name}.\n"
                f"Expected: {expected_columns}\n"
                f"Actual: {actual_columns}"
            )

        actual_rows = connection.execute(
            f"SELECT COUNT(*) FROM raw.{table_name}"
        ).fetchone()[0]

        expected_rows = specification["row_count"]

        if actual_rows != expected_rows:
            raise ValueError(
                f"Row-count failure for raw.{table_name}: "
                f"expected {expected_rows:,}, "
                f"found {actual_rows:,}"
            )

    print("PASS: All raw-table columns and types are correct")
    print("PASS: All six raw-table row counts are correct")


def check_latest_ingestion_log(connection):
    """Confirm that the latest ingestion run logged six successes."""
    log_table_exists = connection.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = 'metadata'
          AND table_name = 'ingestion_log'
          AND table_type = 'BASE TABLE'
        """
    ).fetchone()[0]

    if log_table_exists != 1:
        raise ValueError(
            "Required metadata.ingestion_log table is missing"
        )

    latest_run = connection.execute(
        """
        SELECT run_id
        FROM metadata.ingestion_log
        ORDER BY completed_at DESC
        LIMIT 1
        """
    ).fetchone()

    if latest_run is None:
        raise ValueError(
            "metadata.ingestion_log contains no ingestion records"
        )

    run_id = latest_run[0]

    summary = connection.execute(
        """
        SELECT
            COUNT(*) AS log_rows,
            COUNT(DISTINCT table_name) AS table_count,
            COUNT(*) FILTER (
                WHERE status <> 'SUCCESS'
            ) AS failed_tables,
            COUNT(*) FILTER (
                WHERE actual_rows <> expected_rows
            ) AS row_count_failures
        FROM metadata.ingestion_log
        WHERE run_id = ?
        """,
        [run_id],
    ).fetchone()

    log_rows, table_count, failed_tables, row_count_failures = (
        summary
    )

    if (
        log_rows != 6
        or table_count != 6
        or failed_tables != 0
        or row_count_failures != 0
    ):
        raise ValueError(
            "Latest ingestion metadata is incomplete or failed: "
            f"run_id={run_id}, log_rows={log_rows}, "
            f"tables={table_count}, failed={failed_tables}, "
            f"row_count_failures={row_count_failures}"
        )

    print(
        "PASS: Latest ingestion metadata log contains "
        "six successful table records"
    )


def run_tests():
    """Run structural and SQL data-quality tests against DuckDB."""
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"DuckDB database not found: {DATABASE_PATH}"
        )

    connection = duckdb.connect(
        str(DATABASE_PATH),
        read_only=True,
    )

    failures = 0

    try:
        print("Running DuckDB data-quality tests...\n")

        check_table_structure(connection)
        check_latest_ingestion_log(connection)

        for test_name, query in TESTS:
            issue_count = connection.execute(query).fetchone()[0]

            if issue_count == 0:
                print(f"PASS: {test_name}")
            else:
                print(
                    f"FAIL: {test_name} "
                    f"({issue_count:,} issues)"
                )
                failures += 1

    finally:
        connection.close()

    print()

    if failures:
        raise SystemExit(
            f"{failures} data-quality test(s) failed."
        )

    print("All DuckDB data-quality tests passed.")
    print(
        "Validation rules align with the Data Cleaning notebook: "
        "meaningful first-order nulls and valid statistical "
        "outliers are retained."
    )


if __name__ == "__main__":
    run_tests()
