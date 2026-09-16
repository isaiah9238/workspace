import json
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
        """Runs migration scripts and verifies versions are recorded."""
        self.migrator.run_migrations()
        applied = self.migrator.get_applied_migrations()

        self.assertIn("001", applied)
        self.assertIn("002", applied)
        self.assertIn("003", applied)

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

        cursor.execute("PRAGMA table_info(tools);")
        columns = [row[1] for row in cursor.fetchall()]
        self.assertIn("parameters_json", columns)

    def test_idempotent_migrations(self):
        """Verifies that running migrations a second time does not re-execute already applied versions."""
        first_run = self.migrator.run_migrations()
        self.assertEqual(len(first_run), 3)

        second_run = self.migrator.run_migrations()
        self.assertEqual(len(second_run), 0)

        applied = self.migrator.get_applied_migrations()
        self.assertEqual(len(applied), 3)

    def test_upsert_tool(self):
        """Tests inserting and updating a tool record using upsert_tool."""
        self.migrator.run_migrations()
        from db.tools_repo import upsert_tool

        schema_v1 = {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        }
        upsert_tool(
            self.conn,
            name="read_file",
            description="Reads file contents",
            schema=schema_v1,
        )

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT name, description, parameters_json FROM tools WHERE name = ?",
            ("read_file",),
        )
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "read_file")
        self.assertEqual(row[1], "Reads file contents")
        self.assertEqual(json.loads(row[2]), schema_v1)

        schema_v2 = {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "encoding": {"type": "string"},
            },
            "required": ["path"],
        }
        upsert_tool(
            self.conn,
            name="read_file",
            description="Reads file contents with optional encoding",
            schema=schema_v2,
        )

        cursor.execute("SELECT COUNT(*) FROM tools;")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 1)

        cursor.execute(
            "SELECT name, description, parameters_json FROM tools WHERE name = ?",
            ("read_file",),
        )
        updated_row = cursor.fetchone()
        self.assertEqual(updated_row[1], "Reads file contents with optional encoding")
        self.assertEqual(json.loads(updated_row[2]), schema_v2)

    def test_schema_generator_to_database_integration(self):
        """Integration test: generates schema from source, stores in DB, and asserts deserialized schema properties."""
        from schema_generator import ToolSchemaGenerator
        from db.tools_repo import upsert_tool

        source_code = '''def fetch_user(user_id: int, include_profile: bool = True):
    """Fetches user details from database."""
    pass'''

        schema = ToolSchemaGenerator.generate_from_source(source_code)

        self.migrator.run_migrations()
        description = "Fetches user details from database."
        upsert_tool(
            self.conn,
            name=schema["name"],
            description=description,
            schema=schema,
        )

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT name, description, parameters_json FROM tools WHERE name = ?",
            ("fetch_user",),
        )
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "fetch_user")
        self.assertEqual(row[1], description)

        stored_schema = json.loads(row[2])
        self.assertEqual(stored_schema["name"], "fetch_user")
        self.assertEqual(stored_schema["properties"]["user_id"]["type"], "integer")
        self.assertEqual(
            stored_schema["properties"]["include_profile"]["type"], "boolean"
        )
        self.assertIn("user_id", stored_schema["required"])
        self.assertNotIn("include_profile", stored_schema["required"])


if __name__ == "__main__":
    unittest.main()
