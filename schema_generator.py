import inspect
import re
from typing import Dict, List, get_args, get_origin, get_type_hints

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
        "type": "object",
        "properties": properties,
        "required": required,
    }
