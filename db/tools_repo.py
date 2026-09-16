import json
import sqlite3
from typing import Any, Dict, List, Optional, Union


def upsert_tool(
    conn: sqlite3.Connection,
    name: str,
    description: str,
    schema: dict,
    category: str = "workspace",
    usage_examples: Optional[Union[str, list, dict]] = None,
    target_type: str = "python_function",
) -> None:
    """
    Inserts or updates a tool record in the database with schema and metadata.
    Serializes schema and usage_examples to JSON if structured objects are provided.
    """
    parameters_json = json.dumps(schema) if isinstance(schema, (dict, list)) else schema

    if usage_examples is not None and not isinstance(usage_examples, str):
        usage_examples_str = json.dumps(usage_examples)
    else:
        usage_examples_str = usage_examples

    cursor = conn.cursor()
    cursor.execute("SELECT id FROM tools WHERE name = ?", (name,))
    row = cursor.fetchone()

    if row:
        cursor.execute(
            """
            UPDATE tools
            SET description = ?,
                parameters_json = ?,
                category = ?,
                usage_examples = ?,
                target_type = ?
            WHERE name = ?
            """,
            (description, parameters_json, category, usage_examples_str, target_type, name),
        )
    else:
        cursor.execute(
            """
            INSERT INTO tools (name, description, parameters_json, category, usage_examples, target_type)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, description, parameters_json, category, usage_examples_str, target_type),
        )

    conn.commit()


def get_tool(conn: sqlite3.Connection, name: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a tool by name, automatically deserializing parameters_json and usage_examples.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, name, description, parameters_json, category, usage_examples, target_type
        FROM tools
        WHERE name = ?
        """,
        (name,),
    )
    row = cursor.fetchone()
    if not row:
        return None

    parameters = row[3]
    if parameters and isinstance(parameters, str):
        try:
            parameters = json.loads(parameters)
        except json.JSONDecodeError:
            pass

    usage = row[5]
    if usage and isinstance(usage, str):
        try:
            usage = json.loads(usage)
        except json.JSONDecodeError:
            pass

    return {
        "id": row[0],
        "name": row[1],
        "description": row[2],
        "parameters_json": parameters,
        "category": row[4],
        "usage_examples": usage,
        "target_type": row[6],
    }


def list_tools_by_category(conn: sqlite3.Connection, category: str) -> List[Dict[str, Any]]:
    """
    Retrieves all tools belonging to a given category.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, name, description, parameters_json, category, usage_examples, target_type
        FROM tools
        WHERE category = ?
        """,
        (category,),
    )
    rows = cursor.fetchall()
    results = []
    for row in rows:
        usage = row[5]
        if usage and isinstance(usage, str):
            try:
                usage = json.loads(usage)
            except json.JSONDecodeError:
                pass

        results.append(
            {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "parameters_json": row[3],
                "category": row[4],
                "usage_examples": usage,
                "target_type": row[6],
            }
        )
    return results


# Alias for compatibility
get_tools_by_category = list_tools_by_category
