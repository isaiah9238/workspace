import sqlite3
from db.connection import get_connection
from db.migrator import DatabaseMigrator
from db.seeder import seed_default_tools


def init_database(db_path: str = "app.db") -> sqlite3.Connection:
    """
    Initializes the SQLite database connection, executes pending migrations,
    and seeds default tools if they have not been seeded yet.

    Returns:
        sqlite3.Connection: The active database connection.
    """
    conn = get_connection(db_path)

    migrator = DatabaseMigrator(conn)
    migrator.run_migrations()

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tools WHERE name = 'read_file';")
    row = cursor.fetchone()
    count = row[0] if row else 0

    if count == 0:
        seed_default_tools(conn)

    return conn
