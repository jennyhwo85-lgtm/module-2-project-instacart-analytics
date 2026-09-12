import duckdb

def db_connection(uri: str = "warehouse/instacart.duckdb", read_only: bool = False):

    db = duckdb.connect(uri, read_only=read_only)
    return db

