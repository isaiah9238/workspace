import json
import os
import sqlite3
import unittest
from db.connection import get_connection
from db.migrator import DatabaseMigrator
from db.tool_registry import ToolRegistry


class TestToolRegistry(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")
        self.migrations_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "db", "migrations")
        )
        self.migrator = DatabaseMigrator(
            conn=self.conn, migrations_dir=self.migrations_dir
        )
        self.migrator.run_migrations()
        self.registry = ToolRegistry(conn=self.conn)

    def tearDown(self):
        self.conn.close()

    def test_register_and_get_tool(self):
        """Registers a callable function, verifies schema is saved via upsert_tool into DB, and retrieves callable by name."""
        def add_numbers(a: int, b: int) -> int:
            """Adds two integers."""
            return a + b

        self.registry.register(add_numbers)

        retrieved_func = self.registry.get_tool("add_numbers")
        self.assertEqual(retrieved_func, add_numbers)

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT name, description, parameters_json FROM tools WHERE name = ?",
            ("add_numbers",),
        )
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "add_numbers")
        self.assertEqual(row[1], "Adds two integers.")

        stored_schema = json.loads(row[2])
        self.assertEqual(stored_schema["name"], "add_numbers")
        self.assertEqual(stored_schema["properties"]["a"]["type"], "integer")
        self.assertEqual(stored_schema["properties"]["b"]["type"], "integer")

    def test_execute_tool(self):
        """Executes a registered function through the registry via execute(tool_name, **kwargs) and returns expected result."""
        def multiply(x: int, y: int = 2) -> int:
            """Multiplies x and y."""
            return x * y

        self.registry.register(multiply)
        result = self.registry.execute("multiply", x=5, y=3)
        self.assertEqual(result, 15)

        default_result = self.registry.execute("multiply", x=5)
        self.assertEqual(default_result, 10)

    def test_execute_missing_tool_raises(self):
        """Asserts that calling an unregistered tool raises a KeyError or ValueError."""
        with self.assertRaises((KeyError, ValueError)):
            self.registry.execute("non_existent_tool", param=1)


if __name__ == "__main__":
    unittest.main()
