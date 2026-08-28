import pytest
from django.core.exceptions import ValidationError

from apps.risks.models import RiskLevel, risk_level_for


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (1, RiskLevel.LOW),
        (4, RiskLevel.LOW),
        (5, RiskLevel.MEDIUM),
        (9, RiskLevel.MEDIUM),
        (10, RiskLevel.HIGH),
        (16, RiskLevel.HIGH),
        (17, RiskLevel.CRITICAL),
        (25, RiskLevel.CRITICAL),
    ],
)
def test_risk_matrix_has_approved_boundaries(score: int, expected: RiskLevel) -> None:
    assert risk_level_for(score) == expected


@pytest.mark.parametrize("score", [0, 26])
def test_risk_matrix_rejects_values_outside_five_by_five(score: int) -> None:
    with pytest.raises(ValidationError, match="1 y 25"):
        risk_level_for(score)
