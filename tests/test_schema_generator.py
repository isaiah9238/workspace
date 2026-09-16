import unittest
from typing import Dict, List
from schema_generator import ToolSchemaGenerator, generate_schema


class TestSchemaGenerator(unittest.TestCase):
    def test_primitive_types(self):
        """Asserts that a function with str, int, float, bool maps to string, integer, number, boolean."""
        def sample_function(a: str, b: int, c: float, d: bool):
            pass

        schema = generate_schema(sample_function)
        self.assertEqual(schema["properties"]["a"]["type"], "string")
        self.assertEqual(schema["properties"]["b"]["type"], "integer")
        self.assertEqual(schema["properties"]["c"]["type"], "number")
        self.assertEqual(schema["properties"]["d"]["type"], "boolean")

    def test_required_vs_optional(self):
        """Asserts that parameters without default values are in 'required', and defaulted parameters are not."""
        def sample_function(req1: str, req2: int, opt1: str = "default", opt2: int = 42):
            pass

        schema = generate_schema(sample_function)
        self.assertIn("req1", schema["required"])
        self.assertIn("req2", schema["required"])
        self.assertNotIn("opt1", schema["required"])
        self.assertNotIn("opt2", schema["required"])

    def test_complex_generics(self):
        """Asserts that List[str] maps to type array with items string, and Dict maps to object."""
        def sample_function(items: List[str], mapping: Dict):
            pass

        schema = generate_schema(sample_function)
        self.assertEqual(schema["properties"]["items"]["type"], "array")
        self.assertEqual(schema["properties"]["items"]["items"]["type"], "string")
        self.assertEqual(schema["properties"]["mapping"]["type"], "object")

    def test_docstring_extraction(self):
        """Asserts that parameter docstrings (e.g. Args: param: desc) are placed in the parameter description field."""
        def sample_function(param1: str, param2: int):
            """Sample function.

            Args:
                param1: First parameter description.
                param2: Second parameter description.
            """
            pass

        schema = generate_schema(sample_function)
        self.assertEqual(schema["properties"]["param1"]["description"], "First parameter description.")
        self.assertEqual(schema["properties"]["param2"]["description"], "Second parameter description.")

    def test_ast_source_parsing(self):
        """Asserts that ToolSchemaGenerator.generate_from_source(code_string) returns correct schema from raw source."""
        code_string = """
def calculate_total(price: float, quantity: int, discount: float = 0.0) -> float:
    \"\"\"Calculates total price.

    Args:
        price: Base price of item.
        quantity: Number of items.
        discount: Discount percentage.
    \"\"\"
    return (price * quantity) * (1 - discount)
"""
        schema = ToolSchemaGenerator.generate_from_source(code_string)
        self.assertEqual(schema["name"], "calculate_total")
        self.assertEqual(schema["type"], "object")
        self.assertIn("price", schema["properties"])
        self.assertEqual(schema["properties"]["price"]["type"], "number")
        self.assertIn("quantity", schema["properties"])
        self.assertEqual(schema["properties"]["quantity"]["type"], "integer")
        self.assertIn("discount", schema["properties"])
        self.assertEqual(schema["properties"]["discount"]["type"], "number")
        self.assertIn("price", schema["required"])
        self.assertIn("quantity", schema["required"])
        self.assertNotIn("discount", schema["required"])
        self.assertEqual(schema["properties"]["price"]["description"], "Base price of item.")

    def test_keyword_only_args(self):
        """Tests a function with keyword-only arguments (after a bare *), asserting that required keyword-only args are in 'required' and defaulted keyword-only args are not."""
        def sample_function(pos: int, *, kw_req: str, kw_opt: bool = True):
            pass

        schema = generate_schema(sample_function)
        self.assertIn("kw_req", schema["required"])
        self.assertNotIn("kw_opt", schema["required"])
        self.assertIn("pos", schema["required"])

    def test_union_types(self):
        """Tests a function with a Python 3.10+ pipe union annotation (e.g. value: int | str), asserting it maps to an 'anyOf' schema."""
        def sample_function(value: int | str):
            pass

        schema = generate_schema(sample_function)
        self.assertIn("anyOf", schema["properties"]["value"])
        self.assertEqual(
            schema["properties"]["value"]["anyOf"],
            [{"type": "integer"}, {"type": "string"}]
        )


if __name__ == "__main__":
    unittest.main()
