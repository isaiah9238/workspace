import inspect
import sqlite3
from typing import Any, Callable, Optional
from schema_generator import ToolSchemaGenerator
from db.tools_repo import upsert_tool


class ToolRegistry:
    """
    Registry for managing tool functions, persisting their schemas to SQLite,
    and executing them by name.
    """

    def __init__(self, conn: sqlite3.Connection, migrations_dir: Optional[str] = None):
        self.conn = conn
        self.migrations_dir = migrations_dir
        self._tools: dict[str, Callable] = {}

    def register(self, func: Callable) -> None:
        """
        Generates schema for a callable, persists it to the database via upsert_tool,
        and stores the callable in an internal memory map.
        """
        schema = ToolSchemaGenerator.generate(func)
        name = schema["name"]
        description = inspect.getdoc(func) or ""

        upsert_tool(self.conn, name=name, description=description, schema=schema)
        self._tools[name] = func

    def get_tool(self, name: str) -> Callable:
        """
        Retrieves a registered callable by name, raising KeyError if not found.
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' is not registered.")
        return self._tools[name]

    def execute(self, name: str, **kwargs: Any) -> Any:
        """
        Looks up a registered callable by name and invokes it with kwargs.
        Raises KeyError if the tool is not found.
        """
        func = self.get_tool(name)
        return func(**kwargs)
