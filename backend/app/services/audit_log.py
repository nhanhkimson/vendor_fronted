"""M2 Activity Log queries, export and archive."""

import csv
import io
import json
from datetime import date, datetime, time, timedelta

from sqlalchemy import Select, String, cast, func, or_, select, text
from sqlalchemy.orm import Session

from app.models.system import AuditLog, AuditLogArchive

EXPORT_COLUMNS = [
    "id",
    "at",
    "actor_id",
    "actor_name",
    "actor_roles",
    "actor_vendor_id",
    "ip",
    "user_agent",
    "module",
    "action",
    "resource_type",
    "resource_id",
    "outcome",
    "reason",
    "request_id",
    "before",
    "after",
]


def _filtered(
    model,
    *,
    actor: str | None = None,
    role: str | None = None,
    module: str | None = None,
    action: str | None = None,
    outcome: str | None = None,
    resource: str | None = None,
    q: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> Select:
    stmt = select(model)
    if actor:
        stmt = stmt.where(model.actor_id == actor)
    if role:
        stmt = stmt.where(model.actor_roles.contains([role]))
    if module:
        stmt = stmt.where(model.module == module)
    if action:
        stmt = stmt.where(model.action == action)
    if outcome:
        stmt = stmt.where(model.outcome == outcome)
    if resource:
        stmt = stmt.where(model.resource_id == resource)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(model.actor_name).like(like),
                func.lower(func.coalesce(model.resource_id, "")).like(like),
                func.lower(model.action).like(like),
                func.lower(func.coalesce(model.reason, "")).like(like),
                func.lower(cast(model.after, String)).like(like),
                func.lower(cast(model.before, String)).like(like),
            )
        )
    if date_from:
        stmt = stmt.where(model.at >= datetime.combine(date_from, time.min).astimezone())
    if date_to:
        stmt = stmt.where(model.at < datetime.combine(date_to + timedelta(days=1), time.min).astimezone())
    return stmt


def search(db: Session, *, archive: bool = False, page: int = 1, page_size: int = 50, **filters):
    model = AuditLogArchive if archive else AuditLog
    stmt = _filtered(model, **filters)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(model.at.desc(), model.id.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return {"items": rows, "total": total, "page": page, "page_size": page_size}


def facets(db: Session) -> dict:
    modules = db.scalars(select(AuditLog.module).distinct().order_by(AuditLog.module)).all()
    actions = db.scalars(select(AuditLog.action).distinct().order_by(AuditLog.action)).all()
    actors = db.execute(
        select(AuditLog.actor_id, AuditLog.actor_name)
        .where(AuditLog.actor_id.is_not(None))
        .distinct()
        .order_by(AuditLog.actor_name)
    ).all()
    return {
        "modules": list(modules),
        "actions": list(actions),
        "actors": [{"id": a, "name": n} for a, n in actors],
        "outcomes": ["success", "denied", "failed"],
    }


def export(db: Session, fmt: str, **filters) -> tuple[str, str]:
    rows = db.scalars(_filtered(AuditLog, **filters).order_by(AuditLog.at.desc()).limit(50_000)).all()
    if fmt == "json":
        data = [
            {c: (getattr(r, c).isoformat() if c == "at" else getattr(r, c)) for c in EXPORT_COLUMNS}
            for r in rows
        ]
        return json.dumps(data, indent=2, default=str), "application/json"
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(EXPORT_COLUMNS)
    for r in rows:
        writer.writerow(
            [
                r.id,
                r.at.isoformat(),
                r.actor_id or "",
                r.actor_name,
                "|".join(r.actor_roles or []),
                r.actor_vendor_id or "",
                r.ip or "",
                r.user_agent or "",
                r.module,
                r.action,
                r.resource_type,
                r.resource_id or "",
                r.outcome,
                r.reason or "",
                r.request_id or "",
                json.dumps(r.before, default=str) if r.before is not None else "",
                json.dumps(r.after, default=str) if r.after is not None else "",
            ]
        )
    return buffer.getvalue(), "text/csv"


def archive_all(db: Session) -> int:
    return int(db.execute(text("SELECT archive_audit_logs()")).scalar() or 0)
