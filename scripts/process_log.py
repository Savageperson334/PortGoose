#!/usr/bin/env python3
"""Safe, deterministic math worker for PortGoose.

Reads log.json and writes sandbox.json. It NEVER executes submitted Python code.
Accepted entries: "calc <expression>" and "plot <expression>".
"""
from __future__ import annotations

import ast
import json
import math
import operator
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMAND = re.compile(r"^\s*(calc|plot)\s+(.+?)\s*$", re.IGNORECASE | re.DOTALL)
FUNCTIONS = {
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
    "exp": math.exp, "abs": abs, "floor": math.floor, "ceil": math.ceil,
}
CONSTANTS = {"pi": math.pi, "e": math.e}
BINARY = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.Mod: operator.mod,
}
UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}
LIMIT = 1e12


def finite_number(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Only real numbers are allowed.")
    if not math.isfinite(value) or abs(value) > LIMIT:
        raise ValueError("Result is too large or not finite.")
    return float(value)


def evaluate(expression: str, *, x: float | None = None) -> float:
    """Evaluate a limited numeric expression via AST, never eval/exec."""
    if not 0 < len(expression) <= 120:
        raise ValueError("Expression must be 1–120 characters.")
    expression = expression.replace("^", "**")
    tree = ast.parse(expression, mode="eval")
    if sum(1 for _ in ast.walk(tree)) > 70:
        raise ValueError("Expression is too complex.")

    def visit(node: ast.AST, depth: int = 0) -> float:
        if depth > 24:
            raise ValueError("Expression is too deeply nested.")
        if isinstance(node, ast.Constant):
            return finite_number(node.value)
        if isinstance(node, ast.Name):
            if node.id == "x" and x is not None:
                return finite_number(x)
            if node.id in CONSTANTS:
                return CONSTANTS[node.id]
            raise ValueError("Unknown name: " + node.id)
        if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY:
            return finite_number(UNARY[type(node.op)](visit(node.operand, depth + 1)))
        if isinstance(node, ast.BinOp):
            left = visit(node.left, depth + 1)
            right = visit(node.right, depth + 1)
            if isinstance(node.op, ast.Pow):
                if abs(right) > 32 or abs(left) > 1e6:
                    raise ValueError("Power is outside safe limits.")
                if abs(left) > 1 and right > 0 and right * math.log10(abs(left)) > 12:
                    raise ValueError("Power would exceed the result limit.")
                return finite_number(left ** right)
            if type(node.op) in BINARY:
                return finite_number(BINARY[type(node.op)](left, right))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            name = node.func.id
            if name in FUNCTIONS and len(node.args) == 1 and not node.keywords:
                return finite_number(FUNCTIONS[name](visit(node.args[0], depth + 1)))
        raise ValueError("Unsupported operation or syntax.")

    try:
        return visit(tree.body)
    except (ArithmeticError, OverflowError) as error:
        raise ValueError(str(error)) from error


def process(entries: list[dict]) -> dict:
    """Take the newest calc/plot entry; ignore ordinary text messages."""
    latest = None
    command = None
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        match = COMMAND.fullmatch(str(entry.get("message", "")))
        if match:
            latest, command = entry, match
    if latest is None or command is None:
        return {
            "status": "idle", "operation": None, "expression": None,
            "source_id": None, "message": "Try calc (12+8)*3 or plot sin(x)."
        }

    operation, expression = command.group(1).lower(), command.group(2).strip()
    result = {
        "status": "ok", "operation": operation, "expression": expression,
        "source_id": latest.get("id"), "source_time": latest.get("created_at"),
        "message": "",
    }
    try:
        if operation == "calc":
            result["value"] = evaluate(expression)
        else:
            points = []
            for i in range(81):
                x = -10 + i / 4
                try:
                    y = evaluate(expression, x=x)
                except (ValueError, SyntaxError, TypeError):
                    y = None
                points.append({"x": x, "y": y})
            valid = [point["y"] for point in points if point["y"] is not None]
            if not valid:
                raise ValueError("The expression has no real values on -10 to 10.")
            result["points"] = points
            result["range"] = {"min": min(valid), "max": max(valid)}
    except (ValueError, SyntaxError, TypeError) as error:
        result["status"] = "error"
        result["message"] = str(error)
    return result


def main() -> None:
    entries = json.loads((ROOT / "log.json").read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        raise ValueError("log.json must be an array.")
    result = process(entries)
    result["updated_at"] = datetime.now(timezone.utc).isoformat()
    (ROOT / "sandbox.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(f"Sandbox: {result['status']} / {result['operation']} / {result['expression']}")


if __name__ == "__main__":
    main()
