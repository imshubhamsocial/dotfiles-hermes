from fastmcp import FastMCP
import sympy
from sympy.parsing.sympy_parser import parse_expr
import z3

mcp = FastMCP("symbolic_solver")


@mcp.tool()
def solve_equation(equation: str, variable: str = "x") -> str:
    """Solve an algebraic equation symbolically using SymPy (e.g. 'x**2 - 9 = 0')."""
    var = sympy.Symbol(variable)
    if "=" in equation:
        lhs, rhs = equation.split("=", 1)
        expr = parse_expr(lhs) - parse_expr(rhs)
    else:
        expr = parse_expr(equation)
    solutions = sympy.solve(expr, var)
    return str(solutions)


@mcp.tool()
def check_smt_constraints(constraints: list[str]) -> str:
    """Check boolean/integer constraint satisfiability via Microsoft Z3 SMT solver."""
    solver = z3.Solver()
    vars_dict: dict[str, z3.ArithRef] = {}
    delims = "()+-*<>=!/,"
    for c in constraints:
        s = c
        for d in delims:
            s = s.replace(d, " ")
        for token in s.split():
            if token.isidentifier() and token not in ("and", "or", "not", "True", "False"):
                if token not in vars_dict:
                    vars_dict[token] = z3.Int(token)
    for c in constraints:
        solver.add(eval(c, {"__builtins__": None}, vars_dict))
    if solver.check() == z3.sat:
        return f"SAT: {solver.model()}"
    return "UNSAT"


if __name__ == "__main__":
    mcp.run()
