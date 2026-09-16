import sqlite3
from typing import Any, Dict, List
from db.tools_repo import upsert_tool
from schema_generator import ToolSchemaGenerator


def read_file(file_path: str) -> str:
    """Reads and returns the contents of a file within the workspace.

    Args:
        file_path: Relative path to the file to read.
    """
    pass


def write_file(file_path: str, content: str) -> None:
    """Writes content to a file in the workspace, creating parent directories if needed.

    Args:
        file_path: Relative path to the file to write.
        content: String content to write into the file.
    """
    pass


def run_command(command: str) -> str:
    """Executes a terminal command safely inside the workspace directory after user approval.

    Args:
        command: Shell command to execute.
    """
    pass


def list_files() -> List[str]:
    """Lists all files in the workspace directory recursively, ignoring hidden/git directories."""
    pass


def patch_file(file_path: str, target_snippet: str, replacement_snippet: str) -> None:
    """Replaces an exact text snippet in an existing file with a new snippet.

    Args:
        file_path: Relative path to the target file.
        target_snippet: Exact text snippet to be replaced.
        replacement_snippet: New text snippet to substitute.
    """
    pass


DEFAULT_TOOLS = [
    (
        read_file,
        "workspace",
        [{"input": {"file_path": "README.md"}, "description": "Read file contents"}],
    ),
    (
        write_file,
        "workspace",
        [
            {
                "input": {"file_path": "test.py", "content": "print('hello')"},
                "description": "Write new file",
            }
        ],
    ),
    (
        run_command,
        "workspace",
        [{"input": {"command": "pytest"}, "description": "Run unit tests"}],
    ),
    (
        list_files,
        "workspace",
        [{"input": {}, "description": "List all files in workspace"}],
    ),
    (
        patch_file,
        "workspace",
        [
            {
                "input": {
                    "file_path": "main.py",
                    "target_snippet": "old_code()",
                    "replacement_snippet": "new_code()",
                },
                "description": "Replace text snippet in file",
            }
        ],
    ),
]


def seed_default_tools(conn: sqlite3.Connection) -> None:
    """
    Seeds the default core workspace tools into the database.
    """
    for func, category, usage_examples in DEFAULT_TOOLS:
        schema = ToolSchemaGenerator.generate(func)
        docstring = func.__doc__ or ""
        description = docstring.strip().split("\n")[0] if docstring else func.__name__

        upsert_tool(
            conn=conn,
            name=func.__name__,
            description=description,
            schema=schema,
            category=category,
            usage_examples=usage_examples,
            target_type="python_function",
        )
