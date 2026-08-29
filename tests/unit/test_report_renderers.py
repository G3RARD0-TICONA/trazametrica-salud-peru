from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError

from apps.imports.xlsx import parse_workbook
from apps.reports.renderers import MAX_RENDER_ROWS, render_csv, render_pdf, render_xlsx

COLUMNS = (
    {"name": "synthetic_marker", "type": "text", "required": True},
    {"name": "value", "type": "text", "required": True},
)


def test_csv_is_utf8_stable_and_neutralizes_formulas() -> None:
    content = render_csv(
        columns=COLUMNS,
        rows=[{"synthetic_marker": "DATOS SINTÉTICOS", "value": "=2+2"}],
    )
    assert content.startswith(b"\xef\xbb\xbf")
    decoded = content.decode("utf-8-sig")
    assert decoded.splitlines()[0] == "synthetic_marker,value"
    assert "DATOS SINTÉTICOS,'=2+2" in decoded


def test_xlsx_keeps_marker_contract_and_data() -> None:
    content = render_xlsx(
        contract_code="RPT-TEST",
        version_no=3,
        schema_hash="a" * 64,
        columns=COLUMNS,
        rows=[{"synthetic_marker": "DATOS SINTÉTICOS", "value": "seguro"}],
    )
    workbook = parse_workbook(content)
    assert workbook.marker == "DATOS SINTÉTICOS"
    assert workbook.template_code == "RPT-TEST"
    assert workbook.version_no == 3
    assert workbook.schema_hash == "a" * 64
    assert workbook.headers == ("synthetic_marker", "value")


def test_pdf_is_valid_and_contains_governance_metadata() -> None:
    content = render_pdf(
        title="Reporte sintético",
        contract_code="RPT-TEST",
        version_no=1,
        schema_hash="b" * 64,
        filters_json='{"status":"published"}',
        generated_at="2026-08-28T12:00:00Z",
        columns=COLUMNS,
        rows=[{"synthetic_marker": "DATOS SINTÉTICOS", "value": "42"}],
    )
    assert content.startswith(b"%PDF-1.4")
    assert b"DATOS SINT" in content
    assert b"RPT-TEST v1" in content
    assert b"xref" in content
    assert content.endswith(b"%%EOF\n")


def test_renderer_rejects_more_than_ten_thousand_rows() -> None:
    rows = [
        {"synthetic_marker": "DATOS SINTÉTICOS", "value": index}
        for index in range(MAX_RENDER_ROWS + 1)
    ]
    with pytest.raises(ValidationError, match="10 000"):
        render_csv(columns=COLUMNS, rows=rows)
