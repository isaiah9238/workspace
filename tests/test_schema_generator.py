import unittest
from typing import Dict, List
from schema_generator import generate_schema


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


if __name__ == "__main__":
    unittest.main()
