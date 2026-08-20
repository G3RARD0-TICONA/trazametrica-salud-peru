from datetime import date
from enum import StrEnum

from django.db.models import Q
from django.utils import timezone

from .models import User


class Capability(StrEnum):
    VIEW_DASHBOARD = "accounts.view_dashboard"
    MANAGE_USERS = "accounts.manage_users"
    ASSIGN_ROLES = "accounts.assign_roles"
    APPROVE_ACCESS = "accounts.approve_access"
    MANAGE_ORGANIZATION = "organizations.manage"
    VIEW_ORGANIZATION = "organizations.view"
    DRAFT_PROCESSES = "processes.draft"
    REVIEW_PROCESSES = "processes.review"
    APPROVE_PROCESSES = "processes.approve"
    VIEW_PROCESSES = "processes.view"
    MANAGE_DOCUMENTS = "documents.manage"
    REVIEW_DOCUMENTS = "documents.review"
    APPROVE_DOCUMENTS = "documents.approve"
    CREATE_IMPORTS = "imports.create"
    REVIEW_IMPORTS = "imports.review"
    APPROVE_IMPORTS = "imports.approve"
    DRAFT_INDICATORS = "indicators.draft"
    REVIEW_INDICATORS = "indicators.review"
    PUBLISH_INDICATORS = "indicators.publish"
    PLAN_AUDITS = "audits.plan"
    EXECUTE_AUDITS = "audits.execute"
    REVIEW_AUDITS = "audits.review"
    APPROVE_AUDITS = "audits.approve"
    MANAGE_IMPROVEMENTS = "improvements.manage"
    REVIEW_IMPROVEMENTS = "improvements.review"
    APPROVE_IMPROVEMENTS = "improvements.approve"
    MANAGE_RISKS = "risks.manage"
    REVIEW_RISKS = "risks.review"
    APPROVE_RISKS = "risks.approve"
    VIEW_REPORTS = "reports.view"
    EXPORT_REPORTS = "reports.export"
    VIEW_AUDIT_LOG = "auditlog.view"
    EXPORT_AUDIT_LOG = "auditlog.export"


ROLE_CAPABILITIES: dict[str, frozenset[Capability]] = {
    "ADMIN_SYSTEM": frozenset(
        {
            Capability.VIEW_DASHBOARD,
            Capability.MANAGE_USERS,
            Capability.ASSIGN_ROLES,
            Capability.MANAGE_ORGANIZATION,
            Capability.VIEW_ORGANIZATION,
            Capability.VIEW_AUDIT_LOG,
            Capability.VIEW_REPORTS,
        }
    ),
    "QUALITY_MANAGER": frozenset(
        {
            Capability.VIEW_DASHBOARD,
            Capability.VIEW_ORGANIZATION,
            Capability.DRAFT_PROCESSES,
            Capability.REVIEW_PROCESSES,
            Capability.VIEW_PROCESSES,
            Capability.MANAGE_DOCUMENTS,
            Capability.REVIEW_DOCUMENTS,
            Capability.PLAN_AUDITS,
            Capability.REVIEW_AUDITS,
            Capability.MANAGE_IMPROVEMENTS,
            Capability.REVIEW_IMPROVEMENTS,
            Capability.MANAGE_RISKS,
            Capability.REVIEW_RISKS,
            Capability.VIEW_REPORTS,
            Capability.EXPORT_REPORTS,
            Capability.VIEW_AUDIT_LOG,
        }
    ),
    "PROCESS_OWNER": frozenset(
        {
            Capability.VIEW_DASHBOARD,
            Capability.VIEW_ORGANIZATION,
            Capability.DRAFT_PROCESSES,
            Capability.REVIEW_PROCESSES,
            Capability.VIEW_PROCESSES,
            Capability.MANAGE_DOCUMENTS,
            Capability.MANAGE_IMPROVEMENTS,
            Capability.MANAGE_RISKS,
            Capability.VIEW_REPORTS,
            Capability.EXPORT_REPORTS,
        }
    ),
    "INDICATOR_ANALYST": frozenset(
        {
            Capability.VIEW_DASHBOARD,
            Capability.VIEW_ORGANIZATION,
            Capability.VIEW_PROCESSES,
            Capability.CREATE_IMPORTS,
            Capability.REVIEW_IMPORTS,
            Capability.DRAFT_INDICATORS,
            Capability.REVIEW_INDICATORS,
            Capability.VIEW_REPORTS,
            Capability.EXPORT_REPORTS,
        }
    ),
    "DATA_LOADER": frozenset(
        {
            Capability.VIEW_DASHBOARD,
            Capability.VIEW_ORGANIZATION,
            Capability.CREATE_IMPORTS,
            Capability.VIEW_REPORTS,
        }
    ),
    "AUDITOR": frozenset(
        {
            Capability.VIEW_DASHBOARD,
            Capability.VIEW_ORGANIZATION,
            Capability.VIEW_PROCESSES,
            Capability.EXECUTE_AUDITS,
            Capability.REVIEW_AUDITS,
            Capability.REVIEW_IMPROVEMENTS,
            Capability.REVIEW_RISKS,
            Capability.VIEW_REPORTS,
            Capability.EXPORT_REPORTS,
        }
    ),
    "APPROVER": frozenset(
        {
            Capability.VIEW_DASHBOARD,
            Capability.VIEW_ORGANIZATION,
            Capability.APPROVE_ACCESS,
            Capability.APPROVE_PROCESSES,
            Capability.APPROVE_DOCUMENTS,
            Capability.APPROVE_IMPORTS,
            Capability.PUBLISH_INDICATORS,
            Capability.APPROVE_AUDITS,
            Capability.APPROVE_IMPROVEMENTS,
            Capability.APPROVE_RISKS,
            Capability.VIEW_REPORTS,
            Capability.EXPORT_REPORTS,
            Capability.VIEW_AUDIT_LOG,
            Capability.EXPORT_AUDIT_LOG,
        }
    ),
    "VIEWER": frozenset(
        {
            Capability.VIEW_DASHBOARD,
            Capability.VIEW_ORGANIZATION,
            Capability.VIEW_PROCESSES,
            Capability.VIEW_REPORTS,
            Capability.EXPORT_REPORTS,
        }
    ),
}


def active_role_codes(user: User, on_date: date | None = None) -> set[str]:
    if not user.is_authenticated or not user.is_active:
        return set()
    current_date = on_date or timezone.localdate()
    return set(
        user.role_assignments.filter(
            role__is_active=True,
            valid_from__lte=current_date,
        )
        .filter(Q(valid_to__isnull=True) | Q(valid_to__gte=current_date))
        .values_list("role__code", flat=True)
    )


def capabilities_for_user(user: User, on_date: date | None = None) -> frozenset[Capability]:
    if not user.is_authenticated or not user.is_active:
        return frozenset()
    if user.is_superuser:
        return frozenset(Capability)
    capabilities: set[Capability] = set()
    for role_code in active_role_codes(user, on_date):
        capabilities.update(ROLE_CAPABILITIES.get(role_code, frozenset()))
    return frozenset(capabilities)


def has_capability(user: User, capability: Capability, on_date: date | None = None) -> bool:
    return capability in capabilities_for_user(user, on_date)
