from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.indicators.formulas import (
    evaluate_formula,
    formula_hash,
    formula_roles,
    normalize_formula_ast,
)


def test_formula_is_normalized_hashed_and_evaluated_deterministically() -> None:
    formula = normalize_formula_ast(
        {
            "op": "multiply",
            "args": [
                {
                    "op": "divide",
                    "args": [
                        {"op": "sum", "role": "numerator"},
                        {"op": "sum", "role": "denominator"},
                    ],
                },
                {"op": "constant", "value": "100.000"},
            ],
        }
    )
    inputs = {
        "numerator": [Decimal("20"), Decimal("30")],
        "denominator": [Decimal("100")],
    }
    assert evaluate_formula(formula, inputs) == Decimal("50.000000")
    assert formula_roles(formula) == frozenset({"numerator", "denominator"})
    assert formula_hash(formula) == formula_hash(normalize_formula_ast(formula))


@pytest.mark.parametrize("operator", ["eval", "exec", "python", "sql"])
def test_formula_rejects_executable_or_unknown_operators(operator: str) -> None:
    with pytest.raises(ValidationError, match="no está permitido"):
        normalize_formula_ast({"op": operator, "value": "1"})


def test_formula_rejects_extra_keys_depth_and_role_mismatch() -> None:
    with pytest.raises(ValidationError, match="solo admite"):
        normalize_formula_ast({"op": "sum", "role": "value", "code": "unsafe"})
    nested: object = {"op": "sum", "role": "value"}
    for _ in range(9):
        nested = {"op": "add", "args": [nested, {"op": "constant", "value": "1"}]}
    with pytest.raises(ValidationError, match="niveles"):
        normalize_formula_ast(nested)
    with pytest.raises(ValidationError, match="roles"):
        evaluate_formula({"op": "sum", "role": "value"}, {"other": [Decimal("1")]})


def test_formula_rejects_empty_inputs_zero_division_and_non_finite_constants() -> None:
    with pytest.raises(ValidationError, match="no contiene"):
        evaluate_formula({"op": "average", "role": "value"}, {"value": []})
    with pytest.raises(ValidationError, match="división entre cero"):
        evaluate_formula(
            {
                "op": "divide",
                "args": [
                    {"op": "sum", "role": "value"},
                    {"op": "constant", "value": "0"},
                ],
            },
            {"value": [Decimal("2")]},
        )
    with pytest.raises(ValidationError, match="finita"):
        normalize_formula_ast({"op": "constant", "value": "NaN"})
