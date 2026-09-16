import os
import tempfile
import unittest
from agent import Agent, FunctionCall


class TestAgent(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "agent_test.db")
        self.agent = Agent(db_path=self.db_path)

    def tearDown(self):
        self.agent.conn.close()
        self.temp_dir.cleanup()

    def test_dynamic_tool_execution(self):
        """Verifies that Agent registers core tools and executes them via FunctionCall."""
        # Test write_file
        test_file = os.path.join(self.temp_dir.name, "test.txt")
        fc_write = FunctionCall("write_file", {"file_path": test_file, "content": "hello agent"})
        self.agent.execute_tool(fc_write)

        # Test read_file
        fc_read = FunctionCall("read_file", {"file_path": test_file})
        content = self.agent.execute_tool(fc_read)
        self.assertEqual(content, "hello agent")

        # Test patch_file
        fc_patch = FunctionCall(
            "patch_file",
            {"file_path": test_file, "target_snippet": "hello agent", "replacement_snippet": "hello world"},
        )
        self.agent.execute_tool(fc_patch)

        # Re-read
        updated_content = self.agent.execute_tool(fc_read)
        self.assertEqual(updated_content, "hello world")


if __name__ == "__main__":
    unittest.main()
