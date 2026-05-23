"""Math tools - safe expression evaluation using AST traversal."""

import ast
import operator
import math
import json
from .registry import ToolDef
from ..permissions import Permission

_SAFE_OPERATORS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
    ast.Pow: operator.pow, ast.USub: operator.neg, ast.UAdd: operator.pos,
}
_SAFE_FUNCTIONS = {
    "abs": abs, "round": round, "min": min, "max": max,
    "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "pi": math.pi, "e": math.e, "pow": pow,
}


def _eval_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in _SAFE_FUNCTIONS:
            return _SAFE_FUNCTIONS[node.id]
        raise ValueError(f"Unknown variable: {node.id}")
    if isinstance(node, ast.BinOp):
        op = type(node.op)
        if op not in _SAFE_OPERATORS:
            raise ValueError(f"Unsupported operator: {op.__name__}")
        return _SAFE_OPERATORS[op](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp):
        op = type(node.op)
        if op not in _SAFE_OPERATORS:
            raise ValueError(f"Unsupported operator: {op.__name__}")
        return _SAFE_OPERATORS[op](_eval_node(node.operand))
    if isinstance(node, ast.Call):
        func = _eval_node(node.func)
        if not callable(func):
            raise ValueError(f"Not callable: {func}")
        return func(*[_eval_node(a) for a in node.args])
    raise ValueError(f"Unsupported expression: {ast.dump(node)}")


def safe_eval(expression: str):
    tree = ast.parse(expression, mode="eval")
    return _eval_node(tree.body)


def calculator(params: dict) -> str:
    expr = params.get("expression", "")
    try:
        result = safe_eval(expr)
        return json.dumps({"expression": expr, "result": result})
    except Exception as e:
        return json.dumps({"expression": expr, "error": str(e)})


def get_tools() -> list[ToolDef]:
    return [
        ToolDef(
            name="calculator",
            description="Evaluate a math expression safely. Supports +,-,*,/,**,sqrt,sin,cos,tan,log,abs,round,min,max. Example: '247*893', 'sqrt(144)', 'sin(pi/2)'",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Math expression to evaluate"}
                },
                "required": ["expression"]
            },
            handler=calculator,
            permission=Permission.READ,
        )
    ]
