import os
import sqlite3


class DatabaseMigrator:
    def __init__(self, conn=None, migrations_dir=None):
        if conn is None:
            conn = sqlite3.connect(":memory:")
            conn.row_factory = sqlite3.Row
        self.conn = conn

        if migrations_dir is None:
            migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")
        self.migrations_dir = migrations_dir

    def create_migrations_table(self):
        """Creates the schema_migrations tracking table if it does not exist."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        self.conn.commit()

    def get_applied_migrations(self):
        """Returns a list of applied migration versions."""
        self.create_migrations_table()
        cursor = self.conn.cursor()
        cursor.execute("SELECT version FROM schema_migrations ORDER BY version;")
        rows = cursor.fetchall()
        return [row["version"] if isinstance(row, sqlite3.Row) else row[0] for row in rows]

    def run_migrations(self):
        """Runs all unapplied SQL migration files in the migrations directory."""
        self.create_migrations_table()
        applied = set(self.get_applied_migrations())

        if not os.path.exists(self.migrations_dir):
            return []

        migration_files = sorted(
            [f for f in os.listdir(self.migrations_dir) if f.endswith(".sql")]
        )

        executed = []
        for filename in migration_files:
            version = filename.split("_")[0]
            if version in applied or filename in applied:
                continue

            filepath = os.path.join(self.migrations_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                sql_script = f.read()

            cursor = self.conn.cursor()
            cursor.executescript(sql_script)
            cursor.execute(
                "INSERT INTO schema_migrations (version) VALUES (?);", (version,)
            )
            self.conn.commit()
            executed.append(version)

        return executed

    # Alias for apply_migrations
    def apply_migrations(self):
        return self.run_migrations()
