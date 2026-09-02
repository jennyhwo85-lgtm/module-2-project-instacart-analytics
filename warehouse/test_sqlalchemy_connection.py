from pathlib import Path

from sqlalchemy import create_engine, text


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "Warehouse" / "instacart.duckdb"


engine = create_engine(
    f"duckdb:///{DATABASE_PATH.as_posix()}"
)


with engine.connect() as connection:
    result = connection.execute(
        text(
            """
            SELECT COUNT(*) AS product_rows
            FROM raw.products
            """
        )
    )

    product_rows = result.scalar_one()


print("PASS: SQLAlchemy connected to DuckDB")
print(f"Products found: {product_rows:,}")

print("\nRaw tables:")

with engine.connect() as connection:
    result = connection.execute(
        text(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'raw'
            ORDER BY table_name
            """
        )
    )

    for row in result.mappings():
        print(f"- {row['table_name']}")