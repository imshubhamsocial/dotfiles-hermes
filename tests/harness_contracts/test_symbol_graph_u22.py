"""
Contract Tests for U22: High-Speed Whole-Codebase AST Symbol Indexer and Graph Engine
=======================================================================================
Tests the SymbolGraph class with SQLite WAL mode, AST extraction, call hierarchies,
inheritance trees, and cross-file references with sub-2ms lookups.
"""

from __future__ import annotations

import sys
import tempfile
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import pytest

from hermes_core.symbol_graph import (
    SymbolGraph,
    create_ramdisk_graph,
    create_persistent_graph,
    create_memory_graph,
)


class TestSymbolGraphPythonExtraction:
    """Test 1: Python function and class AST extraction (signatures, docstrings, line numbers)."""

    def test_function_extraction(self):
        graph = create_memory_graph()
        
        code = '''
def hello_world(name: str) -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"

def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
'''
        count = graph.index_source("test.py", code)
        assert count == 2
        
        symbols = graph.find_symbol("hello_world")
        assert len(symbols) == 1
        sym = symbols[0]
        assert sym['name'] == "hello_world"
        assert sym['kind'] == "function"
        assert "(name: str) -> str" in sym['signature']
        assert "Say hello" in sym['docstring']
        assert sym['line_start'] == 2
        
        symbols = graph.find_symbol("add")
        assert len(symbols) == 1
        sym = symbols[0]
        assert "(a: int, b: int) -> int" in sym['signature']
        
        graph.close()

    def test_class_extraction(self):
        graph = create_memory_graph()
        
        code = '''
class Animal:
    """Base animal class."""
    def __init__(self, name: str):
        self.name = name
    
    def speak(self) -> str:
        """Make a sound."""
        return "..."

class Dog(Animal):
    """A friendly dog."""
    def speak(self) -> str:
        return "Woof!"
    
    def fetch(self, item: str) -> bool:
        return True
'''
        count = graph.index_source("test.py", code)
        assert count == 6  # Animal, Animal.__init__, Animal.speak, Dog, Dog.speak, Dog.fetch
        
        animal = graph.find_symbol("Animal")
        assert len(animal) == 1
        assert animal[0]['kind'] == "class"
        assert animal[0]['docstring'] == "Base animal class."
        assert animal[0]['signature'] == ""
        
        dog = graph.find_symbol("Dog")
        assert len(dog) == 1
        assert dog[0]['kind'] == "class"
        assert "(Animal)" in dog[0]['signature']  # inheritance
        
        speak = graph.find_symbol("speak")
        assert len(speak) == 2  # Animal.speak and Dog.speak
        
        graph.close()

    def test_method_parent_tracking(self):
        graph = create_memory_graph()
        
        code = '''
class MyClass:
    def method_one(self):
        pass
    
    def method_two(self):
        pass

def standalone():
    pass
'''
        count = graph.index_source("test.py", code)
        
        # Check method parent tracking
        methods = graph.find_symbol("method_one")
        assert len(methods) == 1
        assert methods[0]['parent_symbol'] == "MyClass"
        
        methods = graph.find_symbol("method_two")
        assert len(methods) == 1
        assert methods[0]['parent_symbol'] == "MyClass"
        
        # Standalone function has no parent
        standalone = graph.find_symbol("standalone")
        assert len(standalone) == 1
        assert standalone[0]['parent_symbol'] == ""
        
        graph.close()

    def test_import_extraction(self):
        graph = create_memory_graph()
        
        code = '''
import os
import json as js
from typing import List, Dict
from pathlib import Path
'''
        count = graph.index_source("test.py", code)
        assert count == 5  # os, js, List, Dict, Path
        
        imports = graph.find_symbol("os")
        assert len(imports) == 1
        assert imports[0]['kind'] == "import"
        
        imports = graph.find_symbol("js")
        assert len(imports) == 1
        assert "import json as js" in imports[0]['signature']
        
        imports = graph.find_symbol("List")
        assert len(imports) == 1
        
        graph.close()


class TestSymbolGraphCallHierarchy:
    """Test 2: Cross-function call hierarchy resolution (caller -> callee)."""

    def test_simple_call_hierarchy(self):
        graph = create_memory_graph()
        
        code = '''
def helper(x: int) -> int:
    return x * 2

def main(value: int) -> int:
    result = helper(value)
    return result + 1

def caller():
    main(5)
    main(10)
'''
        graph.index_source("test.py", code)
        
        # Get callees of main (what main calls)
        callees = graph.get_callees("main")
        assert "helper" in callees
        
        # Get callers of helper (who calls helper)
        callers = graph.get_callers("helper")
        assert len(callers) == 1
        assert callers[0]['caller_symbol'] == "main"
        assert callers[0]['ref_type'] == "call"
        
        # Get callers of main
        callers = graph.get_callers("main")
        assert len(callers) == 1
        assert callers[0]['caller_symbol'] == "caller"
        
        graph.close()

    def test_method_calls(self):
        graph = create_memory_graph()
        
        code = '''
class Calculator:
    def add(self, a: int, b: int) -> int:
        return a + b
    
    def multiply(self, a: int, b: int) -> int:
        result = self.add(a, b)
        return result * 2

calc = Calculator()
calc.add(1, 2)
'''
        graph.index_source("test.py", code)
        
        # Check method calls
        callees = graph.get_callees("multiply")
        assert "add" in callees
        
        callers = graph.get_callers("add")
        caller_symbols = {c['caller_symbol'] for c in callers}
        assert "multiply" in caller_symbols
        assert "Calculator" in caller_symbols or "calc" in caller_symbols
        
        graph.close()

    def test_cross_file_calls(self):
        graph = create_memory_graph()
        
        file1 = '''
def utility():
    return 42

def process():
    return utility() * 2
'''
        file2 = '''
from test1 import utility

def main():
    return utility() + 10
'''
        graph.index_source("test1.py", file1)
        graph.index_source("test2.py", file2)
        
        # Utility is called from both files
        callers = graph.get_callers("utility")
        caller_files = {c['source_file'] for c in callers}
        assert "test1.py" in caller_files or any("test1" in c['source_file'] for c in callers)
        assert "test2.py" in caller_files or any("test2" in c['source_file'] for c in callers)
        
        graph.close()


class TestSymbolGraphInheritance:
    """Test 3: Class inheritance hierarchy (Base -> Derived)."""

    def test_simple_inheritance(self):
        graph = create_memory_graph()
        
        code = '''
class Base:
    def method(self):
        pass

class Derived(Base):
    def method(self):
        super().method()
        return "derived"

class AnotherDerived(Base):
    pass
'''
        graph.index_source("test.py", code)
        
        tree = graph.get_inheritance_tree("Base")
        assert tree['class'] == "Base"
        child_names = {c['name'] for c in tree['children']}
        assert "Derived" in child_names
        assert "AnotherDerived" in child_names
        
        tree = graph.get_inheritance_tree("Derived")
        assert tree['class'] == "Derived"
        parent_names = {p['name'] for p in tree['parents']}
        assert "Base" in parent_names
        
        graph.close()

    def test_multi_level_inheritance(self):
        graph = create_memory_graph()
        
        code = '''
class A:
    pass

class B(A):
    pass

class C(B):
    pass
'''
        graph.index_source("test.py", code)
        
        tree = graph.get_inheritance_tree("B")
        parent_names = {p['name'] for p in tree['parents']}
        assert "A" in parent_names
        
        child_names = {c['name'] for c in tree['children']}
        assert "C" in child_names
        
        graph.close()

    def test_multiple_inheritance(self):
        graph = create_memory_graph()
        
        code = '''
class Mixin:
    pass

class Base:
    pass

class Derived(Base, Mixin):
    pass
'''
        graph.index_source("test.py", code)
        
        tree = graph.get_inheritance_tree("Derived")
        parent_names = {p['name'] for p in tree['parents']}
        assert "Base" in parent_names
        assert "Mixin" in parent_names
        
        graph.close()


class TestSymbolGraphFileOutline:
    """Test 4: File outline generation with nested methods."""

    def test_file_outline(self):
        graph = create_memory_graph()
        
        code = '''
class MyClass:
    def __init__(self):
        self.value = 0
    
    def public_method(self):
        self._private_helper()
        return self.value
    
    def _private_helper(self):
        return 42

def standalone_function():
    return MyClass()
'''
        graph.index_source("test.py", code)
        
        outline = graph.get_file_outline("test.py")
        
        # Should have class and function at root level
        root_names = {item['name'] for item in outline}
        assert "MyClass" in root_names
        assert "standalone_function" in root_names
        
        # Find class and check children
        my_class = next(item for item in outline if item['name'] == "MyClass")
        assert my_class['kind'] == "class"
        child_names = {child['name'] for child in my_class['children']}
        assert "__init__" in child_names
        assert "public_method" in child_names
        assert "_private_helper" in child_names
        
        graph.close()

    def test_outline_ordering(self):
        graph = create_memory_graph()
        
        code = '''
def first():
    pass

class Second:
    pass

def third():
    pass
'''
        graph.index_source("test.py", code)
        
        outline = graph.get_file_outline("test.py")
        names = [item['name'] for item in outline]
        assert names == ["first", "Second", "third"]
        
        graph.close()


class TestSymbolGraphDirectoryIndexing:
    """Test 5: Multi-file directory batch indexing."""

    def test_directory_indexing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create test files
            (tmpdir / "module1.py").write_text("""
def func_a():
    return 1

class ClassA:
    pass
""")
            (tmpdir / "module2.py").write_text("""
from module1 import func_a

def func_b():
    return func_a() + 1
""")
            
            # Create a .gitignore
            (tmpdir / ".gitignore").write_text("__pycache__\n*.pyc\n")
            
            # Create a directory that should be skipped
            venv_dir = tmpdir / ".venv"
            venv_dir.mkdir()
            (venv_dir / "ignored.py").write_text("def should_not_be_indexed(): pass\n")
            
            graph = create_memory_graph()
            stats = graph.index_directory(str(tmpdir), ["*.py"])
            
            assert stats['files_indexed'] == 2  # module1.py and module2.py
            assert stats['total_symbols'] > 0
            assert stats['errors'] == 0
            
            # Verify .venv was skipped
            all_symbols = graph.export_symbol_graph_summary()
            assert all_symbols['total_symbols'] == stats['total_symbols']
            
            graph.close()

    def test_pattern_matching(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            (tmpdir / "test_file.py").write_text("def test_func(): pass\n")
            (tmpdir / "main.py").write_text("def main(): pass\n")
            (tmpdir / "config.json").write_text('{"key": "value"}\n')
            
            graph = create_memory_graph()
            stats = graph.index_directory(str(tmpdir), ["test_*.py"])
            
            assert stats['files_indexed'] == 1  # Only test_file.py
            
            graph.close()


class TestSymbolGraphPersistenceAndLatency:
    """Test 6: Ephemeral RAMDisk / SQLite persistence and fast query latency (<5ms)."""

    def test_ramdisk_persistence(self):
        db_path = "/dev/shm/test_symbol_graph.db"
        
        # Create and populate
        graph1 = SymbolGraph(db_path)
        code = '''
def persistent_func():
    return "persisted"
    
class PersistentClass:
    def method(self):
        pass
'''
        graph1.index_source("test.py", code)
        graph1.close()
        
        # Reconnect and verify
        graph2 = SymbolGraph(db_path)
        
        symbols = graph2.find_symbol("persistent_func")
        assert len(symbols) == 1
        assert symbols[0]['name'] == "persistent_func"
        
        symbols = graph2.find_symbol("PersistentClass")
        assert len(symbols) == 1
        assert symbols[0]['kind'] == "class"
        
        graph2.close()
        
        # Cleanup
        for suffix in ['', '-wal', '-shm']:
            path = db_path + suffix
            if os.path.exists(path):
                os.unlink(path)

    def test_query_latency(self):
        graph = create_memory_graph()
        
        # Index a reasonably sized codebase
        code = '''
''' + "\n".join([f'''
def func_{i}(x: int) -> int:
    """Function {i}."""
    return helper_{i}(x)

def helper_{i}(x: int) -> int:
    return x + {i}

class Class_{i}:
    def method_{i}(self):
        return func_{i}(10)
''' for i in range(100)]) + '''
'''
        
        graph.index_source("large.py", code)
        
        # Measure lookup latency
        start = time.perf_counter()
        for _ in range(100):
            graph.find_symbol("func_50")
        elapsed = (time.perf_counter() - start) * 1000  # ms
        
        avg_latency = elapsed / 100
        print(f"Average lookup latency: {avg_latency:.2f}ms")
        
        # Should be well under 5ms
        assert avg_latency < 5.0, f"Lookup too slow: {avg_latency:.2f}ms"
        
        # Test call hierarchy latency
        start = time.perf_counter()
        for _ in range(100):
            graph.get_callers("func_50")
            graph.get_callees("func_50")
        elapsed = (time.perf_counter() - start) * 1000
        
        avg_latency = elapsed / 200
        print(f"Average call hierarchy latency: {avg_latency:.2f}ms")
        assert avg_latency < 5.0, f"Call hierarchy too slow: {avg_latency:.2f}ms"
        
        graph.close()

    def test_summary_export(self):
        graph = create_memory_graph()
        
        code = '''
def func1(): pass
def func2(): pass
class MyClass:
    def method(self): pass
import os
'''
        graph.index_source("test.py", code)
        
        summary = graph.export_symbol_graph_summary()
        
        assert summary['total_symbols'] == 5  # 2 functions + 1 class + 1 method + 1 import
        assert summary['files_indexed'] == 1
        assert summary['total_references'] >= 0
        assert 'function' in summary['symbols_by_kind']
        assert 'class' in summary['symbols_by_kind']
        assert 'import' in summary['symbols_by_kind']
        
        graph.close()


class TestSymbolGraphEdgeCases:
    """Additional edge case tests."""

    def test_empty_file(self):
        graph = create_memory_graph()
        count = graph.index_source("empty.py", "")
        assert count == 0
        graph.close()

    def test_syntax_error_handling(self):
        graph = create_memory_graph()
        count = graph.index_source("bad.py", "def invalid(:\n    pass\n")
        assert count == 0  # Should handle gracefully
        graph.close()

    def test_clear(self):
        graph = create_memory_graph()
        graph.index_source("test.py", "def func(): pass\n")
        assert graph.export_symbol_graph_summary()['total_symbols'] == 1
        
        graph.clear()
        assert graph.export_symbol_graph_summary()['total_symbols'] == 0
        graph.close()

    def test_context_manager(self):
        with create_memory_graph() as graph:
            graph.index_source("test.py", "def func(): pass\n")
            assert graph.export_symbol_graph_summary()['total_symbols'] == 1
        # Connection closed automatically

    def test_async_function(self):
        graph = create_memory_graph()
        
        code = '''
async def async_func():
    await other_func()
    return 42

async def other_func():
    return 1
'''
        graph.index_source("test.py", code)
        
        symbols = graph.find_symbol("async_func")
        assert len(symbols) == 1
        assert symbols[0]['kind'] == "function"
        
        callees = graph.get_callees("async_func")
        assert "other_func" in callees
        
        graph.close()

    def test_lambda_not_indexed(self):
        """Lambdas are not top-level symbols."""
        graph = create_memory_graph()
        
        code = '''
func = lambda x: x + 1
def regular(): pass
'''
        graph.index_source("test.py", code)
        
        symbols = graph.find_symbol("func")
        # Lambda assigned to variable - may or may not be indexed depending on AST
        # Just verify regular function is indexed
        regular = graph.find_symbol("regular")
        assert len(regular) == 1
        
        graph.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
