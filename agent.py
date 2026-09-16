import os
import sqlite3
import subprocess
from typing import Any, Dict, List, Optional

from db.init_db import init_database
from db.tool_registry import ToolRegistry


# Core workspace tool implementations
def read_file(file_path: str) -> str:
    """Reads and returns the contents of a file within the workspace.

    Args:
        file_path: Relative path to the file to read.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(file_path: str, content: str) -> None:
    """Writes content to a file in the workspace, creating parent directories if needed.

    Args:
        file_path: Relative path to the file to write.
        content: String content to write into the file.
    """
    os_dir = os.path.dirname(file_path)
    if os_dir:
        os.makedirs(os_dir, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def run_command(command: str) -> str:
    """Executes a terminal command safely inside the workspace directory after user approval.

    Args:
        command: Shell command to execute.
    """
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout or result.stderr


def list_files() -> List[str]:
    """Lists all files in the workspace directory recursively, ignoring hidden/git directories."""
    files_list = []
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
        for f in files:
            if not f.startswith(".") and not f.endswith(".pyc"):
                rel_path = os.path.relpath(os.path.join(root, f), ".")
                files_list.append(rel_path)
    return files_list


def patch_file(file_path: str, target_snippet: str, replacement_snippet: str) -> None:
    """Replaces an exact text snippet in an existing file with a new snippet.

    Args:
        file_path: Relative path to the target file.
        target_snippet: Exact text snippet to be replaced.
        replacement_snippet: New text snippet to substitute.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    if target_snippet not in content:
        raise ValueError(f"Target snippet not found in {file_path}")
    new_content = content.replace(target_snippet, replacement_snippet, 1)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)


class FunctionCall:
    """Data representation of a tool call requested by an LLM model."""

    def __init__(self, name: str, args: Optional[Dict[str, Any]] = None):
        self.name = name
        self.args = args or {}


class Agent:
    """Agent that handles dynamic tool registration and execution."""

    def __init__(self, db_path: str = "app.db"):
        self.conn = init_database(db_path)
        self.registry = ToolRegistry(self.conn)
        self._register_core_tools()

    def _register_core_tools(self) -> None:
        """Registers all core workspace tools into the ToolRegistry."""
        for tool_func in [read_file, write_file, patch_file, run_command, list_files]:
            self.registry.register(tool_func)

    def execute_tool(self, function_call: FunctionCall) -> Any:
        """
        Tool execution dispatcher: executes tools dynamically using the ToolRegistry.
        """
        return self.registry.execute(function_call.name, **function_call.args)

    def process_function_calls(self, function_calls: List[FunctionCall]) -> List[Any]:
        """Loops over function calls and executes them dynamically."""
        results = []
        for call in function_calls:
            result = self.execute_tool(call)
            results.append(result)
        return results

from google import genai
from google.genai import types


def run_agent():
    print("--- Initializing Agent Database and Registry ---")
    agent = Agent("app.db")
    client = genai.Client()

    tools_list = [read_file, write_file, patch_file, run_command, list_files]
    chat = client.chats.create(
        model="gemini-3.6-flash",
        config=types.GenerateContentConfig(
            tools=tools_list,
            temperature=0.2,
        ),
    )

    print("--- CodeAgent CLI Ready (type 'exit' or 'quit' to stop) ---")
    while True:
        try:
            user_input = input("\nUser > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit"):
                print("Exiting...")
                break

            response = chat.send_message(user_input)

            while response.function_calls:
                for call in response.function_calls:
                    print(f"[*] Tool Call: {call.name}({call.args})")
                    fc = FunctionCall(name=call.name, args=dict(call.args))
                    output = agent.execute_tool(fc)
                    response = chat.send_message(
                        types.Part.from_function_response(
                            name=call.name,
                            response={"result": str(output)},
                        )
                    )

            if response.text:
                print(f"\nAgent > {response.text}")

        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break
        except Exception as e:
            print(f"[!] Error: {e}")


if __name__ == "__main__":
    run_agent()
