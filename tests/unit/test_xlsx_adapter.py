from __future__ import annotations

import io
import zipfile

import pytest
from django.core.exceptions import ValidationError

from apps.imports.services import normalize_schema, schema_hash
from apps.imports.xlsx import XlsxValidationError, generate_workbook, parse_workbook


def schema() -> dict[str, object]:
    return normalize_schema(
        {
            "columns": [
                {"name": "code", "type": "string", "required": True},
                {"name": "planned_date", "type": "date", "allow_future": True},
            ]
        }
    )


def workbook_bytes() -> bytes:
    definition = schema()
    return generate_workbook(
        template_code="IMP-UNIT",
        version_no=1,
        schema_hash=schema_hash(definition),
        schema=definition,
        data_rows=[["SYN-001", "2027-01-01"]],
    )


def test_generated_xlsx_round_trips_without_external_dependency() -> None:
    parsed = parse_workbook(workbook_bytes())
    assert parsed.marker == "DATOS SINTÉTICOS"
    assert parsed.headers == ("code", "planned_date")
    assert parsed.rows[0].cells[0].value == "SYN-001"
    assert parsed.template_code == "IMP-UNIT"


def test_xlsx_rejects_invalid_container_and_embedded_content() -> None:
    with pytest.raises(XlsxValidationError, match="contenedor"):
        parse_workbook(b"archivo falso")
    source = workbook_bytes()
    output = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(source)) as original, zipfile.ZipFile(output, "w") as altered:
        for info in original.infolist():
            altered.writestr(info, original.read(info.filename))
        altered.writestr("xl/embeddings/object.bin", b"danger")
    with pytest.raises(XlsxValidationError, match="incrustado"):
        parse_workbook(output.getvalue())


def test_schema_rejects_personal_columns_duplicates_and_bad_ranges() -> None:
    with pytest.raises(ValidationError, match="personales"):
        normalize_schema({"columns": [{"name": "dni", "type": "string"}]})
    with pytest.raises(ValidationError, match="duplicada"):
        normalize_schema(
            {
                "columns": [
                    {"name": "code", "type": "string"},
                    {"name": "code", "type": "string"},
                ]
            }
        )
    with pytest.raises(ValidationError, match="invertido"):
        normalize_schema({"columns": [{"name": "value", "type": "decimal", "min": 10, "max": 1}]})


def test_ten_thousand_rows_are_supported() -> None:
    definition = schema()
    content = generate_workbook(
        template_code="IMP-LARGE",
        version_no=1,
        schema_hash=schema_hash(definition),
        schema=definition,
        data_rows=[[f"SYN-{number:05d}", "2027-01-01"] for number in range(10_000)],
    )
    parsed = parse_workbook(content)
    assert len(parsed.rows) == 10_000
