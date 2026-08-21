from datetime import date, timedelta

import pytest

from apps.audits.models import Finding, FindingStatus
from apps.audits.selectors import finding_alert_status


@pytest.mark.parametrize(
    ("offset", "expected"),
    [(-1, "overdue"), (0, "upcoming"), (7, "upcoming"), (8, "on_time")],
)
def test_finding_alert_status(offset: int, expected: str) -> None:
    current = date(2026, 1, 10)
    finding = Finding(status=FindingStatus.OPEN, due_date=current + timedelta(days=offset))
    assert finding_alert_status(finding=finding, on_date=current) == expected
