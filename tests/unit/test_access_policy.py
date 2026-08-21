from datetime import date

from apps.accounts.policies import ROLE_CAPABILITIES, Capability
from apps.accounts.services import date_ranges_overlap


def test_access_model_contains_the_eight_approved_roles() -> None:
    assert set(ROLE_CAPABILITIES) == {
        "ADMIN_SYSTEM",
        "QUALITY_MANAGER",
        "PROCESS_OWNER",
        "INDICATOR_ANALYST",
        "DATA_LOADER",
        "AUDITOR",
        "APPROVER",
        "VIEWER",
    }


def test_approval_is_separated_from_system_administration() -> None:
    assert Capability.APPROVE_PROCESSES not in ROLE_CAPABILITIES["ADMIN_SYSTEM"]
    assert Capability.APPROVE_PROCESSES in ROLE_CAPABILITIES["APPROVER"]
    assert Capability.MANAGE_USERS in ROLE_CAPABILITIES["ADMIN_SYSTEM"]
    assert Capability.MANAGE_USERS not in ROLE_CAPABILITIES["APPROVER"]


def test_date_ranges_include_their_boundaries() -> None:
    first_start = date(2026, 1, 1)
    first_end = date(2026, 1, 31)
    assert date_ranges_overlap(first_start, first_end, date(2026, 1, 31), None)
    assert not date_ranges_overlap(first_start, first_end, date(2026, 2, 1), None)
    assert date_ranges_overlap(first_start, None, date(2030, 1, 1), None)
