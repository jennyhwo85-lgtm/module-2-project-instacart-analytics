import duckdb

def db_connection(uri: str = "warehouse/instacart.duckdb"):

    db = duckdb.connect(uri)
    return db

