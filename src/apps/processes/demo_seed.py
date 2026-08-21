from __future__ import annotations

import uuid
from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.accounts.models import User
from apps.organizations.models import Area, Organization

from .models import (
    Process,
    ProcessType,
    ProcessVersion,
    ProcessVersionStatus,
    SipocEntry,
    SipocEntryType,
)
from .services import process_version_hash

DEMO_NAMESPACE = uuid.UUID("2d97027d-3b66-5c31-a15e-99bdf47eb06e")


def demo_process_uuid(key: str) -> uuid.UUID:
    return uuid.uuid5(DEMO_NAMESPACE, key)


@dataclass(frozen=True)
class ProcessSeed:
    code: str
    name: str
    process_type: ProcessType


def process_catalog() -> tuple[ProcessSeed, ...]:
    groups = (
        ("EST", "Estratégico", ProcessType.STRATEGIC, 10),
        ("OPE", "Operativo", ProcessType.OPERATIONAL, 60),
        ("SOP", "Soporte", ProcessType.SUPPORT, 30),
    )
    return tuple(
        ProcessSeed(
            code=f"{prefix}-{position:03d}",
            name=f"Proceso {label} Sintético {position:03d}",
            process_type=process_type,
        )
        for prefix, label, process_type, count in groups
        for position in range(1, count + 1)
    )


def sipoc_seed(process_code: str) -> tuple[tuple[SipocEntryType, str, str], ...]:
    return (
        (
            SipocEntryType.SUPPLIER,
            f"Proveedor sintético de {process_code}",
            "Origen ficticio del insumo administrativo.",
        ),
        (
            SipocEntryType.INPUT,
            f"Entrada sintética de {process_code}",
            "Información de demostración sin datos personales.",
        ),
        (
            SipocEntryType.ACTIVITY,
            f"Actividad sintética de {process_code}",
            "Transformación administrativa demostrativa.",
        ),
        (
            SipocEntryType.OUTPUT,
            f"Salida sintética de {process_code}",
            "Resultado administrativo ficticio y verificable.",
        ),
        (
            SipocEntryType.CUSTOMER,
            f"Cliente sintético de {process_code}",
            "Receptor ficticio del resultado del proceso.",
        ),
    )


@transaction.atomic
def seed_processes(*, actor: User, dataset_version: str = "1") -> dict[str, int]:
    if dataset_version != "1":
        raise ValidationError("La versión de semilla de procesos no está soportada.")
    organization = Organization.objects.filter(is_active=True).get()
    areas = list(Area.objects.filter(organization=organization, is_active=True).order_by("code"))
    if not areas:
        raise ValidationError("Ejecute primero la semilla organizacional.")

    created_processes = 0
    created_versions = 0
    created_entries = 0
    for index, item in enumerate(process_catalog()):
        process_id = demo_process_uuid(f"process:{item.code}")
        owner_area = areas[index % len(areas)]
        process, created = Process.objects.get_or_create(
            id=process_id,
            defaults={
                "organization": organization,
                "owner_area": owner_area,
                "code": item.code,
                "name": item.name,
                "process_type": item.process_type,
                "created_by": actor,
                "updated_by": actor,
            },
        )
        created_processes += int(created)
        if not created:
            if process.code != item.code or process.organization_id != organization.pk:
                raise ValidationError("La semilla colisiona con un proceso ajeno al dataset.")
            process.owner_area = owner_area
            process.name = item.name
            process.process_type = item.process_type
            process.updated_by = actor
            process.full_clean()
            process.save(
                update_fields=["owner_area", "name", "process_type", "updated_by", "updated_at"]
            )

        version_id = demo_process_uuid(f"process-version:{item.code}:1")
        objective = f"Demostrar de forma sintética el objetivo administrativo de {item.code}."
        scope = f"Desde la entrada ficticia hasta la salida ficticia de {item.code}."
        entries_payload = sorted(
            [
                {
                    "description": description,
                    "entry_type": entry_type,
                    "name": name,
                    "position": 1,
                }
                for entry_type, name, description in sipoc_seed(item.code)
            ],
            key=lambda entry: str(entry["entry_type"]),
        )
        version_hash = process_version_hash(
            process=process,
            version_no=1,
            objective=objective,
            scope=scope,
            entries=entries_payload,
        )
        version, version_created = ProcessVersion.objects.get_or_create(
            id=version_id,
            defaults={
                "process": process,
                "version_no": 1,
                "status": ProcessVersionStatus.DRAFT,
                "objective": objective,
                "scope": scope,
                "version_hash": version_hash,
                "created_by": actor,
                "updated_by": actor,
            },
        )
        created_versions += int(version_created)
        if not version_created and version.status != ProcessVersionStatus.DRAFT:
            continue

        for entry_type, name, description in sipoc_seed(item.code):
            entry_id = demo_process_uuid(f"sipoc:{item.code}:{entry_type}:1")
            _, entry_created = SipocEntry.objects.get_or_create(
                id=entry_id,
                defaults={
                    "process_version": version,
                    "entry_type": entry_type,
                    "position": 1,
                    "name": name,
                    "description": description,
                    "created_by": actor,
                    "updated_by": actor,
                },
            )
            created_entries += int(entry_created)

    return {
        "created_entries": created_entries,
        "created_processes": created_processes,
        "created_versions": created_versions,
        "entries": SipocEntry.objects.filter(
            process_version__process__organization=organization
        ).count(),
        "processes": Process.objects.filter(organization=organization).count(),
        "versions": ProcessVersion.objects.filter(process__organization=organization).count(),
    }
