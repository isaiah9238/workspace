import os
import sqlite3
import tempfile
import unittest


class TestInitDatabase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_tools.db")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_init_database(self):
        """Verifies init_database runs migrations, seeds default tools, and is idempotent."""
        from db.init_db import init_database

        conn = init_database(self.db_path)
        self.assertIsNotNone(conn)

        cursor = conn.cursor()
        cursor.execute("SELECT version FROM schema_migrations ORDER BY version;")
        rows = cursor.fetchall()
        versions = [row[0] for row in rows]
        for expected in ["001", "002", "003", "004"]:
            self.assertIn(expected, versions)

        cursor.execute("SELECT name FROM tools;")
        tool_names = {row[0] for row in cursor.fetchall()}
        expected_tools = {"read_file", "write_file", "patch_file", "run_command", "list_files"}
        self.assertTrue(expected_tools.issubset(tool_names))

        cursor.execute("SELECT COUNT(*) FROM tools;")
        initial_count = cursor.fetchone()[0]

        # Second call to verify idempotence
        conn2 = init_database(self.db_path)
        cursor2 = conn2.cursor()
        cursor2.execute("SELECT COUNT(*) FROM tools;")
        second_count = cursor2.fetchone()[0]

        self.assertEqual(initial_count, second_count)

        conn.close()
        conn2.close()


if __name__ == "__main__":
    unittest.main()
