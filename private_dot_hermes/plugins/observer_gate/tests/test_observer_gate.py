import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from __init__ import check_syntax

class TestObserverGate(unittest.TestCase):
    
    def test_valid_python(self):
        code = "def foo():\n    return 1"
        is_valid, message = check_syntax(code, 'python')
        self.assertTrue(is_valid)
        self.assertEqual(message, "Syntax is valid")

    def test_invalid_python(self):
        code = "def foo():\n    return 1\n}"
        is_valid, message = check_syntax(code, 'python')
        self.assertFalse(is_valid)
        self.assertIn("Python syntax error", message)

    def test_valid_js(self):
        code = "function test() { console.log('hi'); }"
        is_valid, message = check_syntax(code, 'js')
        self.assertTrue(is_valid)
        self.assertEqual(message, "Syntax is valid")

    def test_invalid_js_unbalanced(self):
        code = "function test() { console.log('hi');"
        is_valid, message = check_syntax(code, 'js')
        self.assertFalse(is_valid)
        self.assertIn("Unbalanced delimiters remaining", message)

    def test_invalid_js_mismatched(self):
        code = "function test() { [ console.log('hi') }"
        is_valid, message = check_syntax(code, 'js')
        self.assertFalse(is_valid)
        self.assertIn("Mismatched delimiters", message)

    def test_valid_html(self):
        code = "<html><body><div>Test</div></body></html>"
        is_valid, message = check_syntax(code, 'html')
        self.assertTrue(is_valid)
        self.assertEqual(message, "Syntax is valid")

    def test_invalid_html_unbalanced(self):
        code = "<html><body><div Test</body></html>"
        is_valid, message = check_syntax(code, 'html')
        self.assertFalse(is_valid)
        self.assertIn("Unbalanced delimiters remaining", message)
        
    def test_unsupported_language(self):
        code = "Some unknown code"
        is_valid, message = check_syntax(code, 'cpp')
        self.assertFalse(is_valid)
        self.assertIn("Unsupported language", message)

if __name__ == '__main__':
    unittest.main()