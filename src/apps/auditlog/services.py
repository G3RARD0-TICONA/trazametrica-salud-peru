from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from django.utils import timezone

from apps.accounts.models import User

from .models import AuditEvent, EventResult


def record_event(
    *,
    actor: User | None,
    object_type: str,
    object_id: uuid.UUID | None,
    action: str,
    result: EventResult,
    reason: str = "",
    context: dict[str, Any] | None = None,
    correlation_id: uuid.UUID | None = None,
) -> AuditEvent:
    event_id = uuid.uuid4()
    occurred_at = timezone.now()
    correlation = correlation_id or uuid.uuid4()
    safe_context = context or {}
    payload = {
        "action": action,
        "actor_id": str(actor.pk) if actor else None,
        "context": safe_context,
        "correlation_id": str(correlation),
        "event_id": str(event_id),
        "object_id": str(object_id) if object_id else None,
        "object_type": object_type,
        "occurred_at": occurred_at.isoformat(),
        "reason": reason,
        "result": result,
    }
    event_hash = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()
    event = AuditEvent(
        id=event_id,
        occurred_at=occurred_at,
        actor=actor,
        correlation_id=correlation,
        object_type=object_type,
        object_id=object_id,
        action=action,
        result=result,
        reason=reason.strip(),
        context=safe_context,
        event_hash=event_hash,
    )
    event.full_clean()
    event.save()
    return event
