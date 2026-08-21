from datetime import date, timedelta

import pytest

from apps.accounts.models import User
from apps.improvements.models import CorrectiveAction, CorrectiveActionStatus
from apps.improvements.selectors import corrective_action_alert_status


@pytest.mark.parametrize(
    ("offset", "expected"),
    [(-1, "overdue"), (0, "upcoming"), (7, "upcoming"), (8, "on_time")],
)
def test_corrective_action_alert_status(offset: int, expected: str) -> None:
    current = date(2026, 1, 10)
    action = CorrectiveAction(
        status=CorrectiveActionStatus.IN_PROGRESS,
        due_date=current + timedelta(days=offset),
        owner=User(is_active=True),
    )
    assert corrective_action_alert_status(action=action, on_date=current) == expected


def test_closed_and_inactive_owner_alerts() -> None:
    current = date(2026, 1, 10)
    closed = CorrectiveAction(
        status=CorrectiveActionStatus.CLOSED,
        due_date=current,
        owner=User(is_active=True),
    )
    unassigned = CorrectiveAction(
        status=CorrectiveActionStatus.IN_PROGRESS,
        due_date=current,
        owner=User(is_active=False),
    )
    assert corrective_action_alert_status(action=closed, on_date=current) == "not_applicable"
    assert corrective_action_alert_status(action=unassigned, on_date=current) == "unassigned"
