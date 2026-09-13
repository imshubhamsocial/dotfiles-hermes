from fastmcp import FastMCP
from smolagents import PythonInterpreterTool

mcp = FastMCP("python_eval")
_interpreter = PythonInterpreterTool()


@mcp.tool()
def python_eval(code: str) -> str:
    """Execute Python code in a sandboxed interpreter and return stdout/stderr."""
    return str(_interpreter(code))


if __name__ == "__main__":
    mcp.run()
