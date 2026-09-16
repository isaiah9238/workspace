import json
import sqlite3


def upsert_tool(conn: sqlite3.Connection, name: str, description: str, schema: dict) -> None:
    """
    Inserts or updates a tool record in the database.
    """
    parameters_json = json.dumps(schema)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM tools WHERE name = ?", (name,))
    row = cursor.fetchone()

    if row:
        cursor.execute(
            "UPDATE tools SET description = ?, parameters_json = ? WHERE name = ?",
            (description, parameters_json, name),
        )
    else:
        cursor.execute(
            "INSERT INTO tools (name, description, parameters_json) VALUES (?, ?, ?)",
            (name, description, parameters_json),
        )

    conn.commit()
