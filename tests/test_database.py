import os
import sqlite3
import unittest
from db.connection import get_connection
from db.migrator import DatabaseMigrator


class TestDatabaseMigrator(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")
        self.migrations_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "db", "migrations")
        )
        self.migrator = DatabaseMigrator(
            conn=self.conn, migrations_dir=self.migrations_dir
        )

    def tearDown(self):
        self.conn.close()

    def test_migration_table_created(self):
        """Asserts that running migrations creates a 'schema_migrations' tracking table."""
        self.migrator.run_migrations()
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations';"
        )
        table = cursor.fetchone()
        self.assertIsNotNone(table)
        self.assertEqual(table[0], "schema_migrations")

    def test_apply_migrations(self):
        """Runs two migration scripts (001 creating a 'tools' table, 002 adding an index) and verifies both versions are recorded."""
        self.migrator.run_migrations()
        applied = self.migrator.get_applied_migrations()

        self.assertIn("001", applied)
        self.assertIn("002", applied)

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='tools';"
        )
        tools_table = cursor.fetchone()
        self.assertIsNotNone(tools_table)

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_tools_name';"
        )
        index = cursor.fetchone()
        self.assertIsNotNone(index)

    def test_idempotent_migrations(self):
        """Verifies that running migrations a second time does not re-execute already applied versions."""
        first_run = self.migrator.run_migrations()
        self.assertEqual(len(first_run), 2)

        second_run = self.migrator.run_migrations()
        self.assertEqual(len(second_run), 0)

        applied = self.migrator.get_applied_migrations()
        self.assertEqual(len(applied), 2)


if __name__ == "__main__":
    unittest.main()
