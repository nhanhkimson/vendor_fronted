"""M1 Roles & Permissions: matrix, role CRUD, role hierarchy and assignment guards."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import Ctx, effective_permissions
from app.core.errors import Conflict, NotFound, Unprocessable
from app.core.permissions import CATALOGUE, MODULES, PERMISSION_KEYS
from app.core.util import slugify
from app.models.identity import Permission, Role, RolePermission, User, UserRole

SUPER_ADMIN = "super_admin"


def _holders(db: Session) -> dict[str, int]:
    rows = db.execute(
        select(UserRole.role_id, func.count())
        .join(User, User.id == UserRole.user_id)
        .where(User.is_active.is_(True))
        .group_by(UserRole.role_id)
    ).all()
    return {role_id: count for role_id, count in rows}


def role_out(role: Role, holders: dict[str, int]) -> dict:
    effective = effective_permissions([role])
    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "kind": role.kind,
        "is_system": role.is_system,
        "is_locked": role.is_locked,
        "parent_id": role.parent_id,
        "parent_name": role.parent.name if role.parent else None,
        "user_count": holders.get(role.id, 0),
        "direct": [p.key for p in role.permissions],
        "effective": [
            {"key": key, "source_role_id": source, "inherited": source != role.id}
            for key, source in sorted(effective.items(), key=lambda kv: PERMISSION_KEYS.index(kv[0]))
        ],
    }


def list_roles(db: Session) -> list[dict]:
    holders = _holders(db)
    roles = db.scalars(select(Role).order_by(Role.is_system.desc(), Role.created_at, Role.id)).all()
    return [role_out(r, holders) for r in roles]


def get_role(db: Session, role_id: str) -> Role:
    role = db.get(Role, role_id)
    if role is None:
        raise NotFound("Role", role_id)
    return role


def matrix(db: Session) -> dict:
    return {
        "modules": [{"id": m.id, "code": m.code, "name": m.name} for m in MODULES],
        "permissions": [
            {"key": key, "module": module, "action": action, "description": desc}
            for key, module, action, desc in CATALOGUE
        ],
        "roles": list_roles(db),
    }


def _check_parent(db: Session, role_id: str | None, parent_id: str | None) -> None:
    if parent_id is None:
        return
    parent = db.get(Role, parent_id)
    if parent is None:
        raise Unprocessable(f"Parent role {parent_id} does not exist")
    seen: set[str] = set()
    current: Role | None = parent
    while current is not None and current.id not in seen:
        if role_id is not None and current.id == role_id:
            raise Conflict("That parent would create a loop in the role hierarchy", code="role_cycle")
        seen.add(current.id)
        current = current.parent


def _validate_keys(keys: list[str]) -> list[str]:
    unknown = [k for k in keys if k not in PERMISSION_KEYS]
    if unknown:
        raise Unprocessable(f"Unknown permission keys: {', '.join(unknown)}")
    return sorted(set(keys), key=PERMISSION_KEYS.index)


def create_role(
    ctx: Ctx,
    name: str,
    description: str,
    kind: str,
    parent_id: str | None,
    permissions: list[str],
) -> dict:
    db = ctx.db
    role_id = slugify(name).replace("-", "_")[:40]
    if db.get(Role, role_id) or db.scalar(select(Role).where(func.lower(Role.name) == name.lower())):
        raise Conflict(f"A role called {name} already exists", code="duplicate_role")
    _check_parent(db, None, parent_id)
    keys = _validate_keys(permissions)
    role = Role(id=role_id, name=name, description=description, kind=kind, parent_id=parent_id)
    db.add(role)
    db.flush()
    for key in keys:
        db.add(RolePermission(role_id=role_id, permission_key=key, granted_by=ctx.user_id))
    ctx.audit(
        "roles",
        "create",
        "role",
        role_id,
        after={"name": name, "kind": kind, "parent_id": parent_id, "permissions": keys},
    )
    ctx.commit()
    db.expire_all()
    return role_out(get_role(db, role_id), _holders(db))


def update_role(
    ctx: Ctx, role_id: str, name: str | None, description: str | None, parent_id: str | None, clear_parent: bool
) -> dict:
    db = ctx.db
    role = get_role(db, role_id)
    before = {"name": role.name, "description": role.description, "parent_id": role.parent_id}
    if role.is_locked and (parent_id is not None or clear_parent):
        raise Conflict(f"{role.name} is locked; its hierarchy cannot change", code="role_locked")
    if name and name != role.name:
        clash = db.scalar(select(Role).where(func.lower(Role.name) == name.lower(), Role.id != role_id))
        if clash:
            raise Conflict(f"A role called {name} already exists", code="duplicate_role")
        role.name = name
    if description is not None:
        role.description = description
    if clear_parent:
        role.parent_id = None
    elif parent_id is not None:
        _check_parent(db, role_id, parent_id)
        role.parent_id = parent_id
    after = {"name": role.name, "description": role.description, "parent_id": role.parent_id}
    ctx.audit("roles", "update", "role", role_id, before=before, after=after)
    ctx.commit()
    db.expire_all()
    return role_out(get_role(db, role_id), _holders(db))


def set_permissions(ctx: Ctx, role_id: str, keys: list[str]) -> dict:
    db = ctx.db
    role = get_role(db, role_id)
    if role.is_locked:
        raise Conflict(f"{role.name} is locked so nobody can lock themselves out", code="role_locked")
    wanted = set(_validate_keys(keys))
    current = {p.key for p in role.permissions}
    granted = sorted(wanted - current, key=PERMISSION_KEYS.index)
    revoked = sorted(current - wanted, key=PERMISSION_KEYS.index)
    for key in granted:
        db.add(RolePermission(role_id=role_id, permission_key=key, granted_by=ctx.user_id))
    for key in revoked:
        link = db.get(RolePermission, {"role_id": role_id, "permission_key": key})
        if link:
            db.delete(link)
    for key in granted:
        ctx.audit("roles", "grant", "role", role_id, before=None, after={"permission": key})
    for key in revoked:
        ctx.audit("roles", "revoke", "role", role_id, before={"permission": key}, after=None)
    if not granted and not revoked:
        ctx.audit("roles", "update_permissions", "role", role_id, after={"changed": 0})
    ctx.commit()
    db.expire_all()
    return role_out(get_role(db, role_id), _holders(db))


def toggle_permission(ctx: Ctx, role_id: str, key: str, granted: bool) -> dict:
    role = get_role(ctx.db, role_id)
    current = [p.key for p in role.permissions]
    keys = sorted(set(current) | {key}) if granted else [k for k in current if k != key]
    if key not in PERMISSION_KEYS:
        raise Unprocessable(f"Unknown permission key {key}")
    return set_permissions(ctx, role_id, keys)


def delete_role(ctx: Ctx, role_id: str) -> None:
    db = ctx.db
    role = get_role(db, role_id)
    if role.is_system:
        raise Conflict(f"{role.name} is a system role and cannot be deleted", code="system_role")
    holders = _holders(db).get(role_id, 0)
    if holders:
        raise Conflict(
            f"{role.name} is still assigned to {holders} user(s). Reassign them first.",
            code="role_in_use",
        )
    for child in db.scalars(select(Role).where(Role.parent_id == role_id)).all():
        child.parent_id = None
    before = {"name": role.name, "permissions": [p.key for p in role.permissions]}
    db.delete(role)
    ctx.audit("roles", "delete", "role", role_id, before=before)
    ctx.commit()


def user_out(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "vendor_id": user.vendor_id,
        "is_active": user.is_active,
        "banned": user.is_banned,
        "roles": [{"id": r.id, "name": r.name, "kind": r.kind} for r in user.roles],
        "permissions": sorted(effective_permissions(user.roles), key=PERMISSION_KEYS.index),
    }


def list_users(db: Session, q: str | None, role_id: str | None) -> list[dict]:
    stmt = select(User).order_by(User.name)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(func.lower(User.name).like(like) | func.lower(User.email).like(like))
    if role_id:
        stmt = stmt.where(User.id.in_(select(UserRole.user_id).where(UserRole.role_id == role_id)))
    return [user_out(u) for u in db.scalars(stmt).all()]


def active_super_admins(db: Session) -> int:
    return db.scalar(
        select(func.count())
        .select_from(UserRole)
        .join(User, User.id == UserRole.user_id)
        .where(UserRole.role_id == SUPER_ADMIN, User.is_active.is_(True))
    ) or 0


def assign_roles(ctx: Ctx, user_id: str, role_ids: list[str]) -> dict:
    db = ctx.db
    user = db.get(User, user_id)
    if user is None:
        raise NotFound("User", user_id)
    if not role_ids:
        raise Unprocessable("A user needs at least one role")
    roles = [get_role(db, rid) for rid in dict.fromkeys(role_ids)]
    kinds = {r.kind for r in roles}
    if user.vendor_id and "platform" in kinds:
        raise Conflict("Vendor staff cannot hold platform roles", code="tenancy")
    if "vendor" in kinds and not user.vendor_id:
        raise Conflict("Only users linked to a shop can hold a vendor role", code="tenancy")
    before = [r.id for r in user.roles]
    new_ids = [r.id for r in roles]
    if SUPER_ADMIN in before and SUPER_ADMIN not in new_ids and active_super_admins(db) <= 1:
        raise Conflict(
            "This is the last Super Admin. Promote someone else before removing this role.",
            code="last_super_admin",
        )
    for link in db.scalars(select(UserRole).where(UserRole.user_id == user_id)).all():
        if link.role_id not in new_ids:
            db.delete(link)
    for rid in new_ids:
        if rid not in before:
            db.add(UserRole(user_id=user_id, role_id=rid, assigned_by=ctx.user_id))
    ctx.audit("roles", "assign", "user", user_id, before={"roles": before}, after={"roles": new_ids})
    ctx.commit()
    db.expire_all()
    return user_out(db.get(User, user_id))


def ensure_permission_rows(db: Session) -> None:
    existing = {p.key for p in db.scalars(select(Permission)).all()}
    for index, (key, module, action, desc) in enumerate(CATALOGUE):
        if key not in existing:
            db.add(Permission(key=key, module=module, action=action, description=desc, sort=index))
