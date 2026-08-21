from apps.processes.demo_seed import process_catalog, sipoc_seed
from apps.processes.models import ProcessType, SipocEntryType


def test_demo_catalog_contract_has_expected_distribution() -> None:
    catalog = process_catalog()
    assert len(catalog) == 100
    assert sum(item.process_type == ProcessType.STRATEGIC for item in catalog) == 10
    assert sum(item.process_type == ProcessType.OPERATIONAL for item in catalog) == 60
    assert sum(item.process_type == ProcessType.SUPPORT for item in catalog) == 30
    assert {entry_type for entry_type, _, _ in sipoc_seed("OPE-001")} == set(SipocEntryType)
