import ast
import inspect
import re
import types
from typing import Dict, List, Union, get_args, get_origin, get_type_hints

TYPE_MAP = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    dict: "object",
    Dict: "object",
    list: "array",
    List: "array",
}


def parse_param_docs(docstring):
    """Extracts parameter descriptions from docstrings (e.g., Google or Sphinx style)."""
    if not docstring:
        return {}

    param_docs = {}
    lines = docstring.splitlines()
    in_args_section = False
    current_param = None
    current_desc = []

    for line in lines:
        stripped = line.strip()

        if re.match(r"^(Args|Arguments|Parameters):", stripped, re.IGNORECASE):
            in_args_section = True
            continue
        elif in_args_section and re.match(r"^[A-Z][a-zA-Z0-9_]*:", stripped):
            break

        sphinx_match = re.match(r"^:param\s+([a-zA-Z_]\w*):\s*(.*)", stripped)
        if sphinx_match:
            pname, pdesc = sphinx_match.groups()
            param_docs[pname] = pdesc.strip()
            continue

        if in_args_section:
            param_match = re.match(r"^([a-zA-Z_]\w*)(?:\s*\([^)]*\))?\s*:\s*(.*)", stripped)
            if param_match:
                if current_param and current_desc:
                    param_docs[current_param] = " ".join(current_desc).strip()
                current_param, pdesc = param_match.groups()
                current_desc = [pdesc.strip()] if pdesc else []
            elif current_param and stripped:
                current_desc.append(stripped)

    if current_param and current_desc:
        param_docs[current_param] = " ".join(current_desc).strip()

    return param_docs


def resolve_type(param_type):
    """Resolves Python type annotations to JSON Schema definitions."""
    origin = get_origin(param_type)
    args = get_args(param_type)

    if origin is Union or (hasattr(types, "UnionType") and origin is types.UnionType):
        any_of = [resolve_type(arg) for arg in args]
        return {"anyOf": any_of}

    if origin is None:
        if param_type in TYPE_MAP:
            return {"type": TYPE_MAP[param_type]}
        return {"type": "string"}

    if origin in (list, List):
        if args:
            item_schema = resolve_type(args[0])
            return {"type": "array", "items": item_schema}
        return {"type": "array"}

    if origin in (dict, Dict):
        return {"type": "object"}

    return {"type": "object"}


def ast_annotation_to_schema(node):
    """Converts an AST type annotation node to a JSON schema type definition."""
    if node is None:
        return {"type": "string"}

    type_map = {
        "str": "string",
        "int": "integer",
        "float": "number",
        "bool": "boolean",
        "dict": "object",
        "Dict": "object",
        "list": "array",
        "List": "array",
    }

    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        def flatten_bitor(bnode):
            if isinstance(bnode, ast.BinOp) and isinstance(bnode.op, ast.BitOr):
                return flatten_bitor(bnode.left) + flatten_bitor(bnode.right)
            return [bnode]

        branches = flatten_bitor(node)
        return {"anyOf": [ast_annotation_to_schema(b) for b in branches]}

    if isinstance(node, ast.Name):
        return {"type": type_map.get(node.id, "string")}

    if isinstance(node, ast.Subscript):
        base_id = node.value.id if isinstance(node.value, ast.Name) else ""
        if base_id in ("List", "list"):
            slice_node = node.slice
            if isinstance(slice_node, ast.Index):
                slice_node = slice_node.value
            item_schema = ast_annotation_to_schema(slice_node)
            return {"type": "array", "items": item_schema}
        elif base_id in ("Dict", "dict"):
            return {"type": "object"}

    if isinstance(node, ast.Constant):
        return {"type": type_map.get(str(node.value), "string")}

    return {"type": "string"}


def generate_schema(func):
    """Generates a JSON schema dictionary for a given function based on its type annotations."""
    sig = inspect.signature(func)
    try:
        hints = get_type_hints(func)
    except Exception:
        hints = {}

    docstring = inspect.getdoc(func)
    param_docs = parse_param_docs(docstring)

    properties = {}
    required = []

    for name, param in sig.parameters.items():
        param_type = hints.get(name, param.annotation)
        if param_type is inspect.Parameter.empty:
            param_schema = {"type": "string"}
        else:
            param_schema = resolve_type(param_type)

        if name in param_docs:
            param_schema["description"] = param_docs[name]

        properties[name] = param_schema
        if param.default is inspect.Parameter.empty:
            required.append(name)

    return {
        "name": func.__name__,
        "type": "object",
        "properties": properties,
        "required": required,
    }


class ToolSchemaGenerator:
    """Generator class for creating JSON schemas from callables or source code strings."""

    @classmethod
    def generate(cls, func):
        return generate_schema(func)

    @classmethod
    def generate_from_source(cls, code_string: str) -> dict:
        tree = ast.parse(code_string)
        func_node = None
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_node = node
                break

        if not func_node:
            raise ValueError("No function definition found in source code.")

        docstring = ast.get_docstring(func_node)
        param_docs = parse_param_docs(docstring)

        args = func_node.args
        num_args = len(args.args)
        num_defaults = len(args.defaults)
        num_req = num_args - num_defaults

        properties = {}
        required = []

        for idx, arg in enumerate(args.args):
            pname = arg.arg
            pschema = ast_annotation_to_schema(arg.annotation)
            if pname in param_docs:
                pschema["description"] = param_docs[pname]

            properties[pname] = pschema

            if idx < num_req:
                required.append(pname)

        for arg, default in zip(args.kwonlyargs, args.kw_defaults):
            pname = arg.arg
            pschema = ast_annotation_to_schema(arg.annotation)
            if pname in param_docs:
                pschema["description"] = param_docs[pname]

            properties[pname] = pschema

            if default is None:
                required.append(pname)

        return {
            "name": func_node.name,
            "type": "object",
            "properties": properties,
            "required": required,
        }
