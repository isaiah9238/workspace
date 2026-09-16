import sqlite3


def get_connection(db_path=":memory:"):
    """Returns a new SQLite database connection."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
