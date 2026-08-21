from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass
from typing import Any

from defusedxml.ElementTree import fromstring

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
MAX_XLSX_BYTES = 10 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 50 * 1024 * 1024
MAX_ZIP_ENTRIES = 200
MAX_ROWS = 10_000
MAX_COLUMNS = 100
FORBIDDEN_PARTS = ("vbaproject", "externallinks", "embeddings", "connections", "querytables")
CELL_REFERENCE_PATTERN = re.compile(r"^([A-Z]+)([0-9]+)$")


class XlsxValidationError(ValueError):
    pass


@dataclass(frozen=True)
class WorkbookCell:
    value: str | None
    formula: bool = False


@dataclass(frozen=True)
class WorkbookRow:
    row_number: int
    cells: tuple[WorkbookCell, ...]


@dataclass(frozen=True)
class ParsedWorkbook:
    marker: str
    headers: tuple[str, ...]
    rows: tuple[WorkbookRow, ...]
    template_code: str
    version_no: int
    schema_hash: str


def _xml_text(value: object) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _column_name(position: int) -> str:
    result = ""
    current = position
    while current:
        current, remainder = divmod(current - 1, 26)
        result = chr(65 + remainder) + result
    return result


def _column_index(reference: str) -> int:
    match = CELL_REFERENCE_PATTERN.fullmatch(reference.upper())
    if match is None:
        raise XlsxValidationError("El archivo contiene una referencia de celda inválida.")
    result = 0
    for character in match.group(1):
        result = result * 26 + ord(character) - 64
    if result > MAX_COLUMNS:
        raise XlsxValidationError("El archivo supera el máximo de 100 columnas.")
    return result


def _inline_cell(reference: str, value: object, *, style: int = 1) -> str:
    return f'<c r="{reference}" s="{style}" t="inlineStr"><is><t>{_xml_text(value)}</t></is></c>'


def _sheet_xml(rows: list[list[object]], *, column_count: int) -> str:
    row_xml: list[str] = []
    for row_number, values in enumerate(rows, start=1):
        cells = "".join(
            _inline_cell(f"{_column_name(column)}{row_number}", value)
            for column, value in enumerate(values, start=1)
            if value is not None
        )
        row_xml.append(f'<row r="{row_number}">{cells}</row>')
    max_column = max(column_count, 1)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<worksheet xmlns="{MAIN_NS}">'
        '<sheetViews><sheetView workbookViewId="0"><pane ySplit="2" topLeftCell="A3" '
        'activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>'
        f'<cols><col min="1" max="{max_column}" style="1" width="22" customWidth="1"/></cols>'
        f"<sheetData>{''.join(row_xml)}</sheetData>"
        "</worksheet>"
    )


def _write_part(archive: zipfile.ZipFile, name: str, content: str) -> None:
    info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o600 << 16
    archive.writestr(info, content.encode("utf-8"))


def generate_workbook(
    *,
    template_code: str,
    version_no: int,
    schema_hash: str,
    schema: dict[str, Any],
    data_rows: list[list[object]] | None = None,
) -> bytes:
    columns = schema["columns"]
    headers = [str(column["name"]) for column in columns]
    headers_row: list[object] = list(headers)
    data: list[list[object]] = [["DATOS SINTÉTICOS"], headers_row]
    data.extend(data_rows or [])
    instructions: list[list[object]] = [
        ["DATOS SINTÉTICOS — INSTRUCCIONES"],
        ["Columna", "Tipo", "Obligatoria", "Reglas"],
    ]
    for column in columns:
        rules = []
        for key in ("max_length", "min", "max", "choices", "allow_future", "unique_in_file"):
            if key in column:
                rules.append(f"{key}={column[key]}")
        instructions.append(
            [
                column["name"],
                column["type"],
                "Sí" if column.get("required") else "No",
                "; ".join(rules),
            ]
        )
    metadata: list[list[object]] = [
        ["DATOS SINTÉTICOS — METADATOS"],
        ["template_code", template_code],
        ["version_no", version_no],
        ["schema_hash", schema_hash],
    ]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        _write_part(
            archive,
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '<Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '<Override PartName="/xl/worksheets/sheet3.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            "</Types>",
        )
        _write_part(
            archive,
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            f'<Relationships xmlns="{PKG_REL_NS}">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            "</Relationships>",
        )
        _write_part(
            archive,
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            f'<workbook xmlns="{MAIN_NS}" xmlns:r="{REL_NS}"><sheets>'
            '<sheet name="DATOS" sheetId="1" r:id="rId1"/>'
            '<sheet name="INSTRUCCIONES" sheetId="2" r:id="rId2"/>'
            '<sheet name="META" sheetId="3" r:id="rId3" state="hidden"/>'
            "</sheets></workbook>",
        )
        _write_part(
            archive,
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            f'<Relationships xmlns="{PKG_REL_NS}">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>'
            '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet3.xml"/>'
            '<Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            "</Relationships>",
        )
        _write_part(
            archive,
            "xl/styles.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            f'<styleSheet xmlns="{MAIN_NS}">'
            '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>'
            '<fills count="1"><fill><patternFill patternType="none"/></fill></fills>'
            '<borders count="1"><border/></borders>'
            '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
            '<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
            '<xf numFmtId="49" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/></cellXfs>'
            "</styleSheet>",
        )
        _write_part(
            archive, "xl/worksheets/sheet1.xml", _sheet_xml(data, column_count=len(headers))
        )
        _write_part(
            archive,
            "xl/worksheets/sheet2.xml",
            _sheet_xml(instructions, column_count=4),
        )
        _write_part(archive, "xl/worksheets/sheet3.xml", _sheet_xml(metadata, column_count=2))
    return buffer.getvalue()


def _validate_archive(content: bytes) -> zipfile.ZipFile:
    if not content or len(content) > MAX_XLSX_BYTES:
        raise XlsxValidationError("El archivo XLSX está vacío o supera 10 MiB.")
    if not content.startswith(b"PK"):
        raise XlsxValidationError("El archivo no es un contenedor XLSX válido.")
    try:
        archive = zipfile.ZipFile(io.BytesIO(content), "r")
    except zipfile.BadZipFile as exc:
        raise XlsxValidationError("El archivo XLSX está dañado.") from exc
    infos = archive.infolist()
    if len(infos) > MAX_ZIP_ENTRIES:
        archive.close()
        raise XlsxValidationError("El archivo XLSX contiene demasiadas partes.")
    total_size = 0
    for info in infos:
        lowered = info.filename.casefold()
        if any(part in lowered for part in FORBIDDEN_PARTS):
            archive.close()
            raise XlsxValidationError("El XLSX contiene macros, vínculos o contenido incrustado.")
        if info.filename.startswith("/") or ".." in info.filename.split("/"):
            archive.close()
            raise XlsxValidationError("El XLSX contiene una ruta insegura.")
        total_size += info.file_size
        if info.compress_size and info.file_size / info.compress_size > 100:
            archive.close()
            raise XlsxValidationError("El XLSX presenta una relación de compresión insegura.")
    if total_size > MAX_UNCOMPRESSED_BYTES:
        archive.close()
        raise XlsxValidationError("El XLSX expandido supera el límite de seguridad.")
    return archive


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = fromstring(archive.read("xl/sharedStrings.xml"))
    return [
        "".join(node.text or "" for node in item.findall(f".//{{{MAIN_NS}}}t")) for item in root
    ]


def _sheet_paths(archive: zipfile.ZipFile) -> dict[str, str]:
    workbook = fromstring(archive.read("xl/workbook.xml"))
    relationships = fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    targets: dict[str, str] = {}
    for relationship in relationships:
        if relationship.attrib.get("TargetMode") == "External":
            raise XlsxValidationError("El libro contiene una relación externa.")
        target = relationship.attrib.get("Target", "")
        if target.startswith("/"):
            normalized = target.lstrip("/")
        else:
            normalized = f"xl/{target}"
        targets[relationship.attrib["Id"]] = normalized.replace("xl/../", "")
    result: dict[str, str] = {}
    for sheet in workbook.findall(f".//{{{MAIN_NS}}}sheet"):
        relation_id = sheet.attrib.get(f"{{{REL_NS}}}id", "")
        if relation_id in targets:
            result[sheet.attrib.get("name", "")] = targets[relation_id]
    return result


def _cell_value(cell: Any, shared: list[str]) -> WorkbookCell:
    formula = cell.find(f"{{{MAIN_NS}}}f") is not None
    if formula:
        return WorkbookCell(value=None, formula=True)
    cell_type = cell.attrib.get("t", "n")
    if cell_type == "inlineStr":
        value = "".join(node.text or "" for node in cell.findall(f".//{{{MAIN_NS}}}t"))
        return WorkbookCell(value=value)
    value_node = cell.find(f"{{{MAIN_NS}}}v")
    if value_node is None or value_node.text is None:
        return WorkbookCell(value=None)
    if cell_type == "s":
        try:
            return WorkbookCell(value=shared[int(value_node.text)])
        except (ValueError, IndexError) as exc:
            raise XlsxValidationError("El XLSX contiene una cadena compartida inválida.") from exc
    if cell_type == "b":
        return WorkbookCell(value="true" if value_node.text == "1" else "false")
    return WorkbookCell(value=value_node.text)


def _read_sheet(
    archive: zipfile.ZipFile,
    path: str,
    shared: list[str],
) -> list[WorkbookRow]:
    root = fromstring(archive.read(path))
    result: list[WorkbookRow] = []
    for row in root.findall(f".//{{{MAIN_NS}}}row"):
        row_number = int(row.attrib.get("r", "0"))
        indexed: dict[int, WorkbookCell] = {}
        for cell in row.findall(f"{{{MAIN_NS}}}c"):
            indexed[_column_index(cell.attrib.get("r", ""))] = _cell_value(cell, shared)
        if not indexed:
            continue
        width = max(indexed)
        cells = tuple(indexed.get(index, WorkbookCell(value=None)) for index in range(1, width + 1))
        result.append(WorkbookRow(row_number=row_number, cells=cells))
    return result


def parse_workbook(content: bytes) -> ParsedWorkbook:
    archive = _validate_archive(content)
    try:
        required = {"[Content_Types].xml", "xl/workbook.xml", "xl/_rels/workbook.xml.rels"}
        if not required.issubset(archive.namelist()):
            raise XlsxValidationError("El contenedor no posee la estructura mínima de un XLSX.")
        shared = _shared_strings(archive)
        paths = _sheet_paths(archive)
        if "DATOS" not in paths or "META" not in paths:
            raise XlsxValidationError("El XLSX debe conservar las hojas DATOS y META.")
        data_rows = _read_sheet(archive, paths["DATOS"], shared)
        meta_rows = _read_sheet(archive, paths["META"], shared)
    finally:
        archive.close()
    if len(data_rows) < 2:
        raise XlsxValidationError("La hoja DATOS no contiene marca y encabezados.")
    marker = (data_rows[0].cells[0].value or "").strip()
    headers = tuple((cell.value or "").strip() for cell in data_rows[1].cells)
    if not marker or not any(headers):
        raise XlsxValidationError("La marca sintética o los encabezados están vacíos.")
    rows = tuple(
        row
        for row in data_rows[2:]
        if any(cell.value not in (None, "") or cell.formula for cell in row.cells)
    )
    if len(rows) > MAX_ROWS:
        raise XlsxValidationError("La plantilla supera el máximo de 10 000 filas.")
    metadata: dict[str, str] = {}
    for row in meta_rows[1:]:
        if len(row.cells) >= 2 and row.cells[0].value:
            metadata[row.cells[0].value] = row.cells[1].value or ""
    try:
        version_no = int(metadata["version_no"])
        template_code = metadata["template_code"]
        schema_hash = metadata["schema_hash"]
    except (KeyError, ValueError) as exc:
        raise XlsxValidationError("Los metadatos de plantilla están incompletos.") from exc
    return ParsedWorkbook(
        marker=marker,
        headers=headers,
        rows=rows,
        template_code=template_code,
        version_no=version_no,
        schema_hash=schema_hash,
    )
