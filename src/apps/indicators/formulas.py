from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from decimal import Decimal, DivisionByZero, InvalidOperation, localcontext
from typing import Any

from django.core.exceptions import ValidationError

AGGREGATE_OPERATORS = frozenset({"sum", "average", "minimum", "maximum", "count"})
BINARY_OPERATORS = frozenset({"add", "subtract", "multiply", "divide"})
ALLOWED_OPERATORS = AGGREGATE_OPERATORS | BINARY_OPERATORS | {"constant"}
MAX_FORMULA_DEPTH = 8
MAX_FORMULA_NODES = 64
RESULT_QUANTUM = Decimal("0.000001")
RESULT_LIMIT = Decimal("100000000000000")


def _decimal_text(value: object) -> str:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValidationError("La constante de la fórmula no es decimal.") from exc
    if not number.is_finite():
        raise ValidationError("La constante de la fórmula debe ser finita.")
    normalized = format(number.normalize(), "f")
    return "0" if normalized in {"-0", ""} else normalized


def normalize_formula_ast(formula: object) -> dict[str, Any]:
    counter = 0

    def visit(node: object, depth: int) -> dict[str, Any]:
        nonlocal counter
        counter += 1
        if counter > MAX_FORMULA_NODES:
            raise ValidationError("La fórmula supera 64 nodos.")
        if depth > MAX_FORMULA_DEPTH:
            raise ValidationError("La fórmula supera 8 niveles.")
        if not isinstance(node, dict):
            raise ValidationError("Cada nodo de fórmula debe ser un objeto.")
        operator = str(node.get("op", "")).strip().casefold()
        if operator not in ALLOWED_OPERATORS:
            raise ValidationError(f"El operador {operator!r} no está permitido.")
        if operator == "constant":
            if set(node) != {"op", "value"}:
                raise ValidationError("Una constante solo admite op y value.")
            return {"op": operator, "value": _decimal_text(node["value"])}
        if operator in AGGREGATE_OPERATORS:
            if set(node) != {"op", "role"}:
                raise ValidationError("Un agregado solo admite op y role.")
            role = str(node.get("role", "")).strip().casefold()
            if not role or len(role) > 30 or not role.replace("_", "").isalnum():
                raise ValidationError("El rol de entrada no es válido.")
            return {"op": operator, "role": role}
        if set(node) != {"op", "args"}:
            raise ValidationError("Una operación binaria solo admite op y args.")
        arguments = node.get("args")
        if not isinstance(arguments, list) or len(arguments) != 2:
            raise ValidationError("Una operación binaria requiere exactamente dos argumentos.")
        return {"op": operator, "args": [visit(item, depth + 1) for item in arguments]}

    return visit(formula, 1)


def formula_hash(formula: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(formula, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()


def formula_roles(formula: dict[str, Any]) -> frozenset[str]:
    roles: set[str] = set()

    def visit(node: dict[str, Any]) -> None:
        if node["op"] in AGGREGATE_OPERATORS:
            roles.add(str(node["role"]))
        for child in node.get("args", []):
            visit(child)

    visit(formula)
    return frozenset(roles)


def evaluate_formula(
    formula: dict[str, Any], inputs: Mapping[str, Sequence[Decimal]]
) -> Decimal:
    normalized = normalize_formula_ast(formula)
    expected_roles = formula_roles(normalized)
    if set(inputs) != set(expected_roles):
        raise ValidationError("Los roles de entrada no coinciden con la fórmula.")
    for role, values in inputs.items():
        if not values:
            raise ValidationError(f"El rol {role} no contiene observaciones.")
        if any(not value.is_finite() for value in values):
            raise ValidationError("Las observaciones deben ser decimales finitos.")

    def visit(node: dict[str, Any]) -> Decimal:
        operator = str(node["op"])
        if operator == "constant":
            return Decimal(str(node["value"]))
        if operator in AGGREGATE_OPERATORS:
            values = inputs[str(node["role"])]
            if operator == "sum":
                return sum(values, Decimal(0))
            if operator == "average":
                return sum(values, Decimal(0)) / Decimal(len(values))
            if operator == "minimum":
                return min(values)
            if operator == "maximum":
                return max(values)
            return Decimal(len(values))
        left, right = (visit(child) for child in node["args"])
        if operator == "add":
            return left + right
        if operator == "subtract":
            return left - right
        if operator == "multiply":
            return left * right
        if right == 0:
            raise ValidationError("La fórmula produjo una división entre cero.")
        return left / right

    try:
        with localcontext() as context:
            context.prec = 38
            result = visit(normalized).quantize(RESULT_QUANTUM)
    except (DivisionByZero, InvalidOperation, OverflowError) as exc:
        raise ValidationError("La fórmula produjo un resultado decimal inválido.") from exc
    if not result.is_finite() or abs(result) >= RESULT_LIMIT:
        raise ValidationError("El resultado excede numeric(20,6).")
    return result
