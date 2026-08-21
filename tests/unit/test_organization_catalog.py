from apps.organizations.demo_seed import AREA_CATALOG, SERVICE_COUNTS, SITE_CATALOG, demo_uuid
from apps.organizations.models import ResponsibilityType


def test_demo_catalog_matches_p05_minimums() -> None:
    assert len(SITE_CATALOG) == 3
    assert sum(SERVICE_COUNTS.values()) == 20
    assert len(AREA_CATALOG) == 12


def test_demo_identifiers_are_deterministic() -> None:
    assert demo_uuid("organization:demo") == demo_uuid("organization:demo")
    assert demo_uuid("organization:demo") != demo_uuid("site:SED-01")


def test_responsibility_catalog_is_explicit_and_bounded() -> None:
    assert set(ResponsibilityType.values) == {
        "AREA_OWNER",
        "QUALITY_CONTACT",
        "DATA_STEWARD",
        "BACKUP",
    }
