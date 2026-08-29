from __future__ import annotations

import csv
import io
import textwrap
from collections.abc import Mapping, Sequence
from typing import Any

from django.core.exceptions import ValidationError

from apps.imports.xlsx import generate_workbook

from .models import ExportFormat

SYNTHETIC_MARKER = "DATOS SINTÉTICOS"
MAX_RENDER_ROWS = 10_000


def _ordered_values(
    *, columns: Sequence[Mapping[str, Any]], rows: Sequence[Mapping[str, Any]]
) -> list[list[object]]:
    if len(rows) > MAX_RENDER_ROWS:
        raise ValidationError("La exportación supera el máximo de 10 000 filas.")
    names = [str(column["name"]) for column in columns]
    result: list[list[object]] = []
    for row in rows:
        unknown = set(row) - set(names)
        if unknown:
            raise ValidationError("La consulta produjo columnas fuera del contrato publicado.")
        result.append([row.get(name, "") for name in names])
    return result


def _safe_spreadsheet_text(value: object) -> object:
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@")):
        return f"'{value}"
    return value


def render_csv(*, columns: Sequence[Mapping[str, Any]], rows: Sequence[Mapping[str, Any]]) -> bytes:
    names = [str(column["name"]) for column in columns]
    ordered = _ordered_values(columns=columns, rows=rows)
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerow(names)
    for row in ordered:
        writer.writerow([_safe_spreadsheet_text(value) for value in row])
    return b"\xef\xbb\xbf" + buffer.getvalue().encode("utf-8")


def render_xlsx(
    *,
    contract_code: str,
    version_no: int,
    schema_hash: str,
    columns: Sequence[Mapping[str, Any]],
    rows: Sequence[Mapping[str, Any]],
) -> bytes:
    ordered = _ordered_values(columns=columns, rows=rows)
    safe_rows = [[_safe_spreadsheet_text(value) for value in row] for row in ordered]
    schema = {
        "columns": [
            {
                "name": str(column["name"]),
                "type": str(column["type"]),
                "required": bool(column.get("required", False)),
            }
            for column in columns
        ]
    }
    return generate_workbook(
        template_code=contract_code,
        version_no=version_no,
        schema_hash=schema_hash,
        schema=schema,
        data_rows=safe_rows,
    )


def _pdf_text(value: object) -> str:
    normalized = str(value).replace("\r", " ").replace("\n", " ")
    return normalized.encode("latin-1", errors="replace").decode("latin-1")


def _pdf_literal(value: str) -> bytes:
    escaped = value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return escaped.encode("latin-1", errors="replace")


def _pdf_document(lines: Sequence[str]) -> bytes:
    pages = [list(lines[index : index + 48]) for index in range(0, len(lines), 48)] or [[]]
    page_object_ids = [4 + index * 2 for index in range(len(pages))]
    objects: dict[int, bytes] = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        2: (
            f"<< /Type /Pages /Count {len(pages)} /Kids ["
            + " ".join(f"{object_id} 0 R" for object_id in page_object_ids)
            + "] >>"
        ).encode("ascii"),
        3: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
    }
    for index, page_lines in enumerate(pages):
        page_id = page_object_ids[index]
        content_id = page_id + 1
        stream_parts = [b"BT /F1 9 Tf 40 800 Td 12 TL"]
        for line in page_lines:
            stream_parts.append(b"(" + _pdf_literal(line) + b") Tj T*")
        stream_parts.append(b"ET")
        stream = b"\n".join(stream_parts)
        objects[page_id] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>"
        ).encode("ascii")
        objects[content_id] = (
            f"<< /Length {len(stream)} >>\nstream\n".encode("ascii") + stream + b"\nendstream"
        )
    payload = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for object_id in range(1, max(objects) + 1):
        offsets.append(len(payload))
        payload.extend(f"{object_id} 0 obj\n".encode("ascii"))
        payload.extend(objects[object_id])
        payload.extend(b"\nendobj\n")
    xref_offset = len(payload)
    payload.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    payload.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        payload.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    payload.extend(
        (
            f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(payload)


def render_pdf(
    *,
    title: str,
    contract_code: str,
    version_no: int,
    schema_hash: str,
    filters_json: str,
    generated_at: str,
    columns: Sequence[Mapping[str, Any]],
    rows: Sequence[Mapping[str, Any]],
) -> bytes:
    ordered = _ordered_values(columns=columns, rows=rows)
    names = [str(column["name"]) for column in columns]
    lines = [
        SYNTHETIC_MARKER,
        _pdf_text(title),
        f"Contrato: {contract_code} v{version_no}",
        f"Hash de esquema: {schema_hash}",
        f"Generado UTC: {generated_at}",
        f"Filtros: {_pdf_text(filters_json)}",
        f"Filas: {len(ordered)}",
        "",
        _pdf_text(" | ".join(names)),
    ]
    for row in ordered:
        raw = " | ".join(_pdf_text(value) for value in row)
        lines.extend(textwrap.wrap(raw, width=105, subsequent_indent="  ") or [""])
    return _pdf_document(lines)


def render_export(
    *,
    export_format: str,
    title: str,
    contract_code: str,
    version_no: int,
    schema_hash: str,
    filters_json: str,
    generated_at: str,
    columns: Sequence[Mapping[str, Any]],
    rows: Sequence[Mapping[str, Any]],
) -> bytes:
    if export_format == ExportFormat.CSV:
        return render_csv(columns=columns, rows=rows)
    if export_format == ExportFormat.XLSX:
        return render_xlsx(
            contract_code=contract_code,
            version_no=version_no,
            schema_hash=schema_hash,
            columns=columns,
            rows=rows,
        )
    if export_format == ExportFormat.PDF:
        return render_pdf(
            title=title,
            contract_code=contract_code,
            version_no=version_no,
            schema_hash=schema_hash,
            filters_json=filters_json,
            generated_at=generated_at,
            columns=columns,
            rows=rows,
        )
    raise ValidationError("El formato de exportación no está soportado.")
