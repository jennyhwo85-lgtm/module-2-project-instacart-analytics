from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "warehouse" / "instacart.duckdb"


TESTS = [
    (
        "All six raw tables exist",
        """
        SELECT 6 - COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = 'raw'
          AND table_name IN (
              'aisles',
              'departments',
              'products',
              'orders',
              'order_products_prior',
              'order_products_train'
          )
        """,
    ),
    (
        "Dimension and order primary keys are unique",
        """
        SELECT
            (
                SELECT COUNT(*) - COUNT(DISTINCT aisle_id)
                FROM raw.aisles
            )
          + (
                SELECT COUNT(*) - COUNT(DISTINCT department_id)
                FROM raw.departments
            )
          + (
                SELECT COUNT(*) - COUNT(DISTINCT product_id)
                FROM raw.products
            )
          + (
                SELECT COUNT(*) - COUNT(DISTINCT order_id)
                FROM raw.orders
            )
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
            (
                SELECT COUNT(*)
                FROM raw.aisles
                WHERE aisle_id IS NULL
                   OR aisle IS NULL
            )
          + (
                SELECT COUNT(*)
                FROM raw.departments
                WHERE department_id IS NULL
                   OR department IS NULL
            )
          + (
                SELECT COUNT(*)
                FROM raw.products
                WHERE product_id IS NULL
                   OR product_name IS NULL
                   OR aisle_id IS NULL
                   OR department_id IS NULL
            )
          + (
                SELECT COUNT(*)
                FROM raw.orders
                WHERE order_id IS NULL
                   OR user_id IS NULL
                   OR eval_set IS NULL
                   OR order_number IS NULL
                   OR order_dow IS NULL
                   OR order_hour_of_day IS NULL
            )
          + (
                SELECT COUNT(*)
                FROM raw.order_products_prior
                WHERE order_id IS NULL
                   OR product_id IS NULL
                   OR add_to_cart_order IS NULL
                   OR reordered IS NULL
            )
          + (
                SELECT COUNT(*)
                FROM raw.order_products_train
                WHERE order_id IS NULL
                   OR product_id IS NULL
                   OR add_to_cart_order IS NULL
                   OR reordered IS NULL
            )
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


def run_tests():
    """Run data-quality tests against the DuckDB raw tables."""
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


if __name__ == "__main__":
    run_tests()