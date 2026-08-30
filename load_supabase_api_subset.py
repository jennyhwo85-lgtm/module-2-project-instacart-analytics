from __future__ import annotations

import argparse
import json
import math
import os
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIRECTORY = PROJECT_ROOT / "supabase_import"
CHECKPOINT_PATH = DATA_DIRECTORY / ".api_load_checkpoint.json"

DEFAULT_BATCH_SIZE = 1_000
MAX_RETRIES = 5

TABLES = {
    "aisles": {
        "filename": "aisles.csv",
        "conflict": "aisle_id",
    },
    "departments": {
        "filename": "departments.csv",
        "conflict": "department_id",
    },
    "products": {
        "filename": "products.csv",
        "conflict": "product_id",
    },
    "orders": {
        "filename": "orders.csv",
        "conflict": "order_id",
    },
    "order_products_prior": {
        "filename": "order_products__prior.csv",
        "conflict": "order_id,product_id",
    },
    "order_products_train": {
        "filename": "order_products__train.csv",
        "conflict": "order_id,product_id",
    },
}


def load_checkpoint() -> dict[str, int]:
    if not CHECKPOINT_PATH.exists():
        return {}

    return json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))


def save_checkpoint(checkpoint: dict[str, int]) -> None:
    temporary_path = CHECKPOINT_PATH.with_suffix(".tmp")

    temporary_path.write_text(
        json.dumps(checkpoint, indent=2),
        encoding="utf-8",
    )

    temporary_path.replace(CHECKPOINT_PATH)


def count_rows(csv_path: Path) -> int:
    with csv_path.open("rb") as csv_file:
        return max(sum(1 for _ in csv_file) - 1, 0)


def upload_batch(
    session: requests.Session,
    api_url: str,
    headers: dict[str, str],
    table_name: str,
    conflict_columns: str,
    payload: str,
) -> None:
    retryable_statuses = {408, 429, 500, 502, 503, 504}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = session.post(
                f"{api_url}/rest/v1/{table_name}",
                headers=headers,
                params={"on_conflict": conflict_columns},
                data=payload,
                timeout=120,
            )
        except requests.RequestException as error:
            if attempt == MAX_RETRIES:
                raise RuntimeError(
                    f"Network failure after {MAX_RETRIES} attempts: {error}"
                ) from error

            wait_seconds = min(2**attempt, 30)
            print(
                f"  Network error. Retrying in {wait_seconds} seconds..."
            )
            time.sleep(wait_seconds)
            continue

        if response.ok:
            return

        if (
            response.status_code not in retryable_statuses
            or attempt == MAX_RETRIES
        ):
            raise RuntimeError(
                f"API error {response.status_code}: "
                f"{response.text[:1_000]}"
            )

        wait_seconds = min(2**attempt, 30)

        print(
            f"  API status {response.status_code}. "
            f"Retrying in {wait_seconds} seconds..."
        )

        time.sleep(wait_seconds)


def upload_table(
    session: requests.Session,
    api_url: str,
    headers: dict[str, str],
    table_name: str,
    batch_size: int,
    checkpoint: dict[str, int],
) -> None:
    configuration = TABLES[table_name]
    csv_path = DATA_DIRECTORY / configuration["filename"]

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    total_rows = count_rows(csv_path)
    total_batches = math.ceil(total_rows / batch_size)
    completed_batches = checkpoint.get(table_name, 0)

    print()
    print(f"Table: {table_name}")
    print(f"Rows: {total_rows:,}")
    print(f"Batches: {total_batches:,}")
    print(f"Previously completed: {completed_batches:,}")

    chunks = pd.read_csv(
        csv_path,
        chunksize=batch_size,
        low_memory=False,
    )

    for batch_number, chunk in enumerate(chunks, start=1):
        if batch_number <= completed_batches:
            continue

        payload = chunk.to_json(orient="records")

        upload_batch(
            session=session,
            api_url=api_url,
            headers=headers,
            table_name=table_name,
            conflict_columns=configuration["conflict"],
            payload=payload,
        )

        checkpoint[table_name] = batch_number
        save_checkpoint(checkpoint)

        if (
            batch_number == 1
            or batch_number % 25 == 0
            or batch_number == total_batches
        ):
            uploaded_rows = min(
                batch_number * batch_size,
                total_rows,
            )

            print(
                f"  Progress: {uploaded_rows:,}/{total_rows:,} "
                f"rows ({batch_number:,}/{total_batches:,} batches)"
            )

    print(f"Completed: {table_name}")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Load the Pipeline 2 CSV subset into the "
            "Supabase public schema."
        )
    )

    selection = parser.add_mutually_exclusive_group(required=True)

    selection.add_argument(
        "--table",
        choices=TABLES.keys(),
        help="Upload one table.",
    )

    selection.add_argument(
        "--all",
        action="store_true",
        help="Upload all six tables.",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="Rows sent in each API request.",
    )

    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()

    load_dotenv(
    dotenv_path=PROJECT_ROOT / ".env",
    override=True,
)

    api_url = os.getenv("SUPABASE_API_LOAD_URL")
    secret_key = os.getenv("SUPABASE_API_LOAD_SECRET_KEY")

    if not api_url:
        raise RuntimeError("SUPABASE_API_LOAD_URL is missing from .env")

    if not secret_key:
        raise RuntimeError("SUPABASE_API_LOAD_SECRET_KEY is missing from .env")

    if arguments.batch_size < 1:
        raise ValueError("Batch size must be greater than zero.")

    api_url = api_url.rstrip("/")

    headers = {
        "apikey": secret_key,
        "Content-Type": "application/json",
        "Content-Profile": "public",
        "Accept-Profile": "public",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }

    selected_tables = (
        list(TABLES)
        if arguments.all
        else [arguments.table]
    )

    checkpoint = load_checkpoint()

    with requests.Session() as session:
        for table_name in selected_tables:
            upload_table(
                session=session,
                api_url=api_url,
                headers=headers,
                table_name=table_name,
                batch_size=arguments.batch_size,
                checkpoint=checkpoint,
            )

    print()
    print("Selected API uploads completed successfully.")
    print(f"Checkpoint: {CHECKPOINT_PATH}")


if __name__ == "__main__":
    main()