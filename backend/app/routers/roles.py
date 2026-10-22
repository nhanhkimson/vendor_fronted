from fastapi import APIRouter, Depends, Query

from app.core.deps import Ctx, audit_meta, require
from app.schemas.common import Message
from app.schemas.identity import (
    MatrixOut,
    RoleCreate,
    RoleOut,
    RolePermissionsIn,
    RoleUpdate,
    UserOut,
    UserRolesIn,
)
from app.services import rbac

router = APIRouter(prefix="/api", tags=["M1 Roles & Permissions"])


@router.get("/permissions", response_model=MatrixOut, summary="Permission catalogue and role matrix")
def permission_matrix(ctx: Ctx = Depends(require("role:read"))):
    return rbac.matrix(ctx.db)


@router.get("/roles", response_model=list[RoleOut], summary="List roles with direct and inherited permissions")
def list_roles(ctx: Ctx = Depends(require("role:read"))):
    return rbac.list_roles(ctx.db)


@router.post(
    "/roles",
    response_model=RoleOut,
    status_code=201,
    summary="Create a custom role",
    openapi_extra=audit_meta("roles", "create"),
)
def create_role(body: RoleCreate, ctx: Ctx = Depends(require("role:create"))):
    return rbac.create_role(ctx, body.name, body.description, body.kind, body.parent_id, body.permissions)


@router.get("/roles/{role_id}", response_model=RoleOut, summary="One role")
def get_role(role_id: str, ctx: Ctx = Depends(require("role:read"))):
    return rbac.role_out(rbac.get_role(ctx.db, role_id), rbac._holders(ctx.db))


@router.patch(
    "/roles/{role_id}",
    response_model=RoleOut,
    summary="Rename a role or change its parent (inheritance)",
    openapi_extra=audit_meta("roles", "update"),
)
def update_role(role_id: str, body: RoleUpdate, ctx: Ctx = Depends(require("role:update"))):
    return rbac.update_role(ctx, role_id, body.name, body.description, body.parent_id, body.clear_parent)


@router.put(
    "/roles/{role_id}/permissions",
    response_model=RoleOut,
    summary="Replace a role's direct permissions",
    description="Each granted or revoked key is written to the activity log separately.",
    openapi_extra=audit_meta("roles", "update_permissions"),
)
def replace_permissions(role_id: str, body: RolePermissionsIn, ctx: Ctx = Depends(require("role:update"))):
    return rbac.set_permissions(ctx, role_id, body.permissions)


@router.post(
    "/roles/{role_id}/permissions/{key}",
    response_model=RoleOut,
    summary="Grant one permission",
    openapi_extra=audit_meta("roles", "grant"),
)
def grant_permission(role_id: str, key: str, ctx: Ctx = Depends(require("role:update"))):
    return rbac.toggle_permission(ctx, role_id, key, True)


@router.delete(
    "/roles/{role_id}/permissions/{key}",
    response_model=RoleOut,
    summary="Revoke one permission (takes effect on the holder's next request)",
    openapi_extra=audit_meta("roles", "revoke"),
)
def revoke_permission(role_id: str, key: str, ctx: Ctx = Depends(require("role:update"))):
    return rbac.toggle_permission(ctx, role_id, key, False)


@router.delete(
    "/roles/{role_id}",
    response_model=Message,
    summary="Delete a custom role that nobody holds",
    openapi_extra=audit_meta("roles", "delete"),
)
def delete_role(role_id: str, ctx: Ctx = Depends(require("role:delete"))):
    rbac.delete_role(ctx, role_id)
    return Message(detail=f"Role {role_id} deleted")


@router.get("/users", response_model=list[UserOut], summary="Users and their roles")
def list_users(
    q: str | None = Query(default=None, description="Name or email contains"),
    role: str | None = Query(default=None, description="Only users holding this role id"),
    ctx: Ctx = Depends(require("role:read")),
):
    return rbac.list_users(ctx.db, q, role)


@router.put(
    "/users/{user_id}/roles",
    response_model=UserOut,
    summary="Assign roles to a user",
    description="Refuses to remove the last Super Admin and keeps vendor staff out of platform roles.",
    openapi_extra=audit_meta("roles", "assign"),
)
def assign_roles(user_id: str, body: UserRolesIn, ctx: Ctx = Depends(require("user:assign_role"))):
    return rbac.assign_roles(ctx, user_id, body.role_ids)
