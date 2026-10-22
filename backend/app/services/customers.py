"""M8 customers: accounts, spend, and ban with a reason."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import utcnow
from app.core.deps import Ctx
from app.core.errors import Conflict, NotFound
from app.core.security import hash_password
from app.core.util import new_id, snapshot
from app.models import Order, Review, Role, User, UserRole
from app.services.events import Notice, emit


def _customer_ids(db: Session):
    return select(UserRole.user_id).join(Role, Role.id == UserRole.role_id).where(Role.kind == "customer")


def _stats(db: Session) -> tuple[dict, dict]:
    orders = {
        buyer: (int(n), int(spent or 0))
        for buyer, n, spent in db.execute(
            select(Order.buyer_id, func.count(Order.id), func.sum(Order.total_cents)).group_by(Order.buyer_id)
        )
    }
    reviews = {buyer: int(n) for buyer, n in db.execute(select(Review.buyer_id, func.count(Review.id)).group_by(Review.buyer_id))}
    return orders, reviews


def customer_out(user: User, orders: dict, reviews: dict) -> dict:
    count, spent = orders.get(user.id, (0, 0))
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "city": user.city,
        "source": user.source,
        "blurb": user.blurb,
        "is_active": user.is_active,
        "banned": user.is_banned,
        "ban_reason": user.ban_reason,
        "created_at": user.created_at,
        "last_login_at": user.last_login_at,
        "orders": count,
        "spent_cents": spent,
        "reviews": reviews.get(user.id, 0),
    }


def list_customers(db: Session, q: str | None, source: str | None, banned: bool | None, include_inactive: bool) -> list[dict]:
    query = select(User).where(User.id.in_(_customer_ids(db))).order_by(User.created_at.desc())
    if q:
        like = f"%{q.lower()}%"
        query = query.where(func.lower(User.name).like(like) | func.lower(User.email).like(like) | func.lower(User.city).like(like))
    if source:
        query = query.where(User.source == source)
    if banned is True:
        query = query.where(User.banned_at.is_not(None))
    elif banned is False:
        query = query.where(User.banned_at.is_(None))
    if not include_inactive:
        query = query.where(User.is_active.is_(True))
    users = db.scalars(query).all()
    orders, reviews = _stats(db)
    return [customer_out(u, orders, reviews) for u in users]


def get_customer(db: Session, user_id: str) -> User:
    user = db.get(User, user_id)
    if user is None or user.id not in set(db.scalars(_customer_ids(db)).all()):
        raise NotFound("Customer", user_id)
    return user


def detail(db: Session, user_id: str) -> dict:
    user = get_customer(db, user_id)
    orders, reviews = _stats(db)
    body = customer_out(user, orders, reviews)
    recent = db.scalars(select(Order).where(Order.buyer_id == user.id).order_by(Order.placed_at.desc()).limit(8)).all()
    body["recent_orders"] = [{"id": o.id, "status": o.status, "total_cents": o.total_cents, "placed_at": o.placed_at} for o in recent]
    return body


def _not_staff(user: User) -> None:
    kinds = {role.kind for role in user.roles}
    if kinds - {"customer"}:
        raise Conflict("This account is staff or a seller. Change their role instead.", code="not_a_customer")


def create_customer(ctx: Ctx, body) -> dict:
    db = ctx.db
    if db.scalar(select(User).where(func.lower(User.email) == body.email)):
        raise Conflict("An account with that email already exists", code="email_taken")
    user = User(
        id=new_id("U"),
        email=body.email,
        password_hash=hash_password(body.password),
        name=body.name.strip(),
        city=body.city,
        source=body.source,
        blurb=body.blurb or "Added by Bazaar staff",
    )
    db.add(user)
    db.flush()
    db.add(UserRole(user_id=user.id, role_id="customer", assigned_by=ctx.user_id))
    db.refresh(user)
    ctx.audit("customer", "create", "user", user.id, after={"email": user.email, "source": user.source})
    ctx.commit()
    return customer_out(user, {}, {})


def update_customer(ctx: Ctx, user_id: str, body) -> dict:
    db = ctx.db
    user = get_customer(db, user_id)
    changes = body.model_dump(exclude_unset=True)
    if "email" in changes and changes["email"] and changes["email"] != user.email:
        taken = db.scalar(select(User.id).where(func.lower(User.email) == changes["email"], User.id != user.id))
        if taken:
            raise Conflict("An account with that email already exists", code="email_taken")
    before = snapshot(user, ["name", "email", "city", "source", "blurb"])
    for field in ("name", "email", "city", "source", "blurb"):
        if field in changes and changes[field] is not None:
            setattr(user, field, changes[field].strip() if isinstance(changes[field], str) else changes[field])
    ctx.audit("customer", "update", "user", user.id, before=before, after=snapshot(user, ["name", "email", "city", "source", "blurb"]))
    ctx.commit()
    orders, reviews = _stats(db)
    return customer_out(user, orders, reviews)


def ban(ctx: Ctx, user_id: str, reason: str, *, lift: bool) -> dict:
    db = ctx.db
    user = get_customer(db, user_id)
    if user.id == ctx.user_id:
        raise Conflict("You can't change the ban on your own account", code="self_target")
    _not_staff(user)
    if lift:
        if not user.is_banned:
            raise Conflict(f"{user.name} is not banned", code="not_banned")
        before = {"banned": True, "ban_reason": user.ban_reason}
        user.banned_at = None
        user.ban_reason = None
        action = "unban"
        title = "Your account restriction was lifted"
    else:
        if user.is_banned:
            raise Conflict(f"{user.name} is already banned", code="already_banned")
        before = {"banned": False}
        user.banned_at = utcnow()
        user.ban_reason = reason.strip()
        action = "ban"
        title = f"Your account is restricted: {user.ban_reason}"
    ctx.audit("customer", action, "user", user.id, before=before, after={"banned": user.is_banned, "ban_reason": user.ban_reason}, reason=reason)
    emit(db, f"customer.{action}", {"user_id": user.id}, [Notice(user.id, title, "/account")])
    ctx.commit()
    orders, reviews = _stats(db)
    return customer_out(user, orders, reviews)


def deactivate(ctx: Ctx, user_id: str, reason: str) -> dict:
    db = ctx.db
    user = get_customer(db, user_id)
    if user.id == ctx.user_id:
        raise Conflict("You can't deactivate your own account", code="self_target")
    _not_staff(user)
    if not user.is_active:
        raise Conflict(f"{user.name} is already deactivated", code="already_inactive")
    user.is_active = False
    ctx.audit("customer", "deactivate", "user", user.id, before={"is_active": True}, after={"is_active": False}, reason=reason)
    ctx.commit()
    orders, reviews = _stats(db)
    return customer_out(user, orders, reviews)
