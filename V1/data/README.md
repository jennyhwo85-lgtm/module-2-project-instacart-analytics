# Dataset

Raw CSVs are **not** committed to this repository (large files, and per the project's need-not-want / lean-repo principle).

## Source

Instacart Market Basket Analysis dataset (Kaggle):
https://www.kaggle.com/datasets/psparks/instacart-market-basket-analysis/data

## Files expected in this folder (git-ignored)

- `orders.csv`
- `products.csv`
- `aisles.csv`
- `departments.csv`
- `order_products__prior.csv`
- `order_products__train.csv`

## Setup instructions

1. Download the dataset from the Kaggle link above (requires a free Kaggle account).
2. Unzip and place the six CSV files directly into this `data/` folder.
3. Do not commit these files — they are covered by `.gitignore`.
4. Run the ingestion script in `src/` to load them into the warehouse (BigQuery). See root `README.md` §4 for the pipeline overview.

## Row counts (for verification after download)

| File | Rows | Columns |
|---|---:|---:|
| `orders.csv` | 3,421,083 | 7 |
| `products.csv` | 49,688 | 4 |
| `aisles.csv` | 134 | 2 |
| `departments.csv` | 21 | 2 |
| `order_products__prior.csv` | 32,434,489 | 4 |
| `order_products__train.csv` | 1,384,617 | 4 |

Full column-level definitions: [`../docs/DATA_DICTIONARY.md`](../docs/DATA_DICTIONARY.md) §1.`
