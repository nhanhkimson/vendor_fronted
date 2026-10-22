"""M3 Vendors: applications, documents, verification, suspension, tiers, guarded delete."""

from fastapi import UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.db import system_scope, utcnow
from app.core.deps import Ctx
from app.core.errors import Conflict, NotFound, Unprocessable
from app.core.util import new_id, slugify, snapshot
from app.domain.states import VENDOR
from app.models import (
    CommissionRule,
    CommissionTier,
    Payout,
    Product,
    SubOrder,
    User,
    UserRole,
    Vendor,
    VendorDocument,
    VendorStatusEvent,
    Warehouse,
)
from app.services import files
from app.services.events import Notice, emit, users_with_permission, vendor_staff_ids
from app.services.present import product_counts, shop_card

REQUIRED_DOCUMENTS = [
    ("government_id", "Government ID"),
    ("address_proof", "Address proof"),
    ("payout_account", "Payout account token"),
]
OPEN_SUB_ORDER = ("pending_acceptance", "accepted", "packing", "shipped")
UNPAID_PAYOUT = ("requested", "pending_second_approval", "approved")
WAREHOUSE_BY_COUNTRY = {"US": "WH-EAST", "CA": "WH-CA", "UK": "WH-UK"}
EDITABLE = ["name", "city", "headline", "about", "shipping_fee_cents", "processing_days", "warehouse_id", "internal_notes"]
SHOP_EDITABLE = ["headline", "about", "city", "shipping_fee_cents", "processing_days", "payout_account"]
STATUS_ACTIONS = {
    "draft": ["submit"],
    "rejected": ["submit"],
    "under_review": ["verify", "reject"],
    "active": ["suspend"],
    "suspended": ["reinstate"],
}


def document_out(doc: VendorDocument) -> dict:
    return {
        "id": doc.id,
        "kind": doc.kind,
        "name": doc.name,
        "status": doc.status,
        "original_filename": doc.original_filename,
        "uploaded_at": doc.uploaded_at,
        "reviewed_by": doc.reviewed_by,
        "reviewed_at": doc.reviewed_at,
        "has_file": bool(doc.file_path),
    }


def vendor_out(db: Session, vendor: Vendor, *, staff_view: bool) -> dict:
    data = shop_card(vendor, product_counts(db).get(vendor.id, 0))
    open_subs = db.scalar(
        select(func.count()).select_from(SubOrder).where(
            SubOrder.vendor_id == vendor.id, SubOrder.status.in_(OPEN_SUB_ORDER)
        )
    )
    history = db.scalars(
        select(VendorStatusEvent).where(VendorStatusEvent.vendor_id == vendor.id).order_by(VendorStatusEvent.at)
    ).all()
    staff = db.scalars(select(User).where(User.vendor_id == vendor.id).order_by(User.name)).all()
    data.update(
        status=vendor.status,
        status_reason=vendor.status_reason,
        verified_at=vendor.verified_at,
        warehouse_id=vendor.warehouse_id,
        warehouse_name=vendor.warehouse.name if vendor.warehouse else None,
        payout_account=vendor.payout_account,
        internal_notes=vendor.internal_notes if staff_view else None,
        is_outlier=vendor.is_outlier,
        response_flag=vendor.response_flag,
        deleted_at=vendor.deleted_at,
        created_at=vendor.created_at,
        open_sub_orders=int(open_subs or 0),
        staff=[{"id": u.id, "name": u.name, "email": u.email} for u in staff],
        documents=[document_out(d) for d in vendor.documents],
        history=[
            {"from_status": e.from_status, "to_status": e.to_status, "actor_id": e.actor_id, "reason": e.reason, "at": e.at}
            for e in history
        ],
        allowed_actions=[] if vendor.deleted_at else STATUS_ACTIONS.get(vendor.status, []),
    )
    return data


def tiers(db: Session) -> list[dict]:
    rates = {
        r.target_id: r.rate_bps
        for r in db.scalars(
            select(CommissionRule).where(CommissionRule.target_type == "tier", CommissionRule.effective_to.is_(None))
        ).all()
    }
    return [
        {"id": t.id, "name": t.name, "name_kh": t.name_kh, "min_sales": t.min_sales, "max_sales": t.max_sales, "rate_bps": rates.get(t.id)}
        for t in db.scalars(select(CommissionTier).order_by(CommissionTier.sort)).all()
    ]


def get_vendor(db: Session, vendor_id: str) -> Vendor:
    vendor = db.get(Vendor, vendor_id)
    if vendor is None:
        raise NotFound("Vendor", vendor_id)
    return vendor


def list_vendors(db: Session, status: str | None, q: str | None, tier: str | None, include_deleted: bool) -> list[dict]:
    query = select(Vendor).order_by(Vendor.name)
    if status:
        query = query.where(Vendor.status == status)
    if tier:
        query = query.where(Vendor.tier_id == tier)
    if q:
        like = f"%{q.lower()}%"
        query = query.where(or_(func.lower(Vendor.name).like(like), func.lower(Vendor.city).like(like), Vendor.id == q))
    if not include_deleted:
        query = query.where(Vendor.deleted_at.is_(None))
    return [vendor_out(db, v, staff_view=True) for v in db.scalars(query).all()]


def _unique_slug(db: Session, name: str) -> str:
    slug = slugify(name)
    if db.scalar(select(Vendor).where(Vendor.slug == slug)):
        raise Conflict(f"A shop called {name} already exists. Pick another name.", code="duplicate_shop")
    return slug


def _event(db: Session, vendor: Vendor, from_status: str | None, to_status: str, actor: str | None, reason: str | None):
    db.add(
        VendorStatusEvent(
            vendor_id=vendor.id, from_status=from_status, to_status=to_status, actor_id=actor, reason=reason, at=utcnow()
        )
    )


def _attach_owner(db: Session, user: User, vendor_id: str, assigned_by: str | None) -> None:
    if user.vendor_id:
        raise Conflict(f"{user.name} already runs a shop", code="already_vendor")
    if any(r.kind == "platform" for r in user.roles):
        raise Conflict("Platform staff cannot run a shop", code="tenancy")
    user.vendor_id = vendor_id
    if not any(r.id == "vendor" for r in user.roles):
        db.add(UserRole(user_id=user.id, role_id="vendor", assigned_by=assigned_by))


def _new_documents(db: Session, vendor_id: str) -> list[VendorDocument]:
    docs = []
    for kind, name in REQUIRED_DOCUMENTS:
        doc = VendorDocument(id=new_id("DOC", 6), vendor_id=vendor_id, kind=kind, name=name, status="missing")
        db.add(doc)
        docs.append(doc)
    return docs


def _notify_reviewers(db: Session, vendor: Vendor) -> None:
    emit(
        db,
        "vendor.submitted",
        {"vendor_id": vendor.id, "name": vendor.name},
        [
            Notice(user_id, f"{vendor.name} submitted documents for review", "/admin/vendors")
            for user_id in users_with_permission(db, "vendor:verify")
        ],
    )


def create_vendor(ctx: Ctx, body) -> dict:
    db = ctx.db
    vendor = Vendor(
        id=new_id("V", 6),
        name=body.name.strip(),
        slug=_unique_slug(db, body.name),
        country=body.country.upper(),
        city=body.city,
        headline=body.headline,
        about=body.about,
        shipping_fee_cents=body.shipping_fee_cents,
        status="draft",
        tier_id="starter",
        warehouse_id=WAREHOUSE_BY_COUNTRY.get(body.country.upper(), "WH-EAST"),
        image_url=None,
        hue=sum(map(ord, body.name)) % 360,
        since=utcnow().date(),
    )
    db.add(vendor)
    db.flush()
    _new_documents(db, vendor.id)
    _event(db, vendor, None, "draft", ctx.user_id, "Created by staff")
    if body.owner_user_id:
        owner = db.get(User, body.owner_user_id)
        if owner is None:
            raise Unprocessable(f"User {body.owner_user_id} does not exist")
        _attach_owner(db, owner, vendor.id, ctx.user_id)
    ctx.audit("vendor", "create", "vendor", vendor.id, after=snapshot(vendor, ["name", "country", "status", "tier_id"]) | {"owner": body.owner_user_id})
    ctx.commit()
    db.expire_all()
    return vendor_out(db, get_vendor(db, vendor.id), staff_view=True)


def update_vendor(ctx: Ctx, vendor_id: str, body) -> dict:
    db = ctx.db
    vendor = get_vendor(db, vendor_id)
    changes = body.model_dump(exclude_unset=True)
    if "warehouse_id" in changes and changes["warehouse_id"] and not db.get(Warehouse, changes["warehouse_id"]):
        raise Unprocessable(f"Warehouse {changes['warehouse_id']} does not exist")
    if "name" in changes and changes["name"] != vendor.name:
        vendor.slug = _unique_slug(db, changes["name"])
    before = snapshot(vendor, EDITABLE)
    for field, value in changes.items():
        setattr(vendor, field, value)
    ctx.audit("vendor", "update", "vendor", vendor_id, before=before, after=snapshot(vendor, EDITABLE))
    ctx.commit()
    return vendor_out(db, vendor, staff_view=True)


def _move(ctx: Ctx, vendor: Vendor, target: str, reason: str | None, action: str) -> None:
    if vendor.deleted_at:
        raise Conflict(f"{vendor.name} was deleted", code="vendor_deleted")
    before = vendor.status
    VENDOR.check(before, target, vendor.name)
    vendor.status = target
    vendor.status_reason = reason
    if target == "active" and before == "under_review":
        vendor.verified_at = utcnow()
    _event(ctx.db, vendor, before, target, ctx.user_id, reason)
    ctx.audit("vendor", action, "vendor", vendor.id, before={"status": before}, after={"status": target}, reason=reason)


def verify(ctx: Ctx, vendor_id: str) -> dict:
    db = ctx.db
    vendor = get_vendor(db, vendor_id)
    pending = [d.name for d in vendor.documents if d.status != "verified"]
    if pending and vendor.status == "under_review":
        raise Conflict(
            f"Approve every document first. Still to review: {', '.join(pending)}.",
            code="documents_pending",
            details={"documents": pending},
        )
    _move(ctx, vendor, "active", "Documents verified", "verify")
    emit(
        db,
        "vendor.verified",
        {"vendor_id": vendor.id},
        [Notice(uid, f"{vendor.name} is verified. Your shop is live.", "/seller") for uid in vendor_staff_ids(db, vendor.id)],
    )
    ctx.commit()
    return vendor_out(db, vendor, staff_view=True)


def reject(ctx: Ctx, vendor_id: str, reason: str) -> dict:
    db = ctx.db
    vendor = get_vendor(db, vendor_id)
    _move(ctx, vendor, "rejected", reason, "reject")
    emit(
        db,
        "vendor.rejected",
        {"vendor_id": vendor.id, "reason": reason},
        [Notice(uid, f"Application needs changes: {reason}", "/seller/storefront") for uid in vendor_staff_ids(db, vendor.id)],
    )
    ctx.commit()
    return vendor_out(db, vendor, staff_view=True)


def suspend(ctx: Ctx, vendor_id: str, reason: str) -> dict:
    db = ctx.db
    vendor = get_vendor(db, vendor_id)
    _move(ctx, vendor, "suspended", reason, "suspend")
    emit(
        db,
        "vendor.suspended",
        {"vendor_id": vendor.id, "reason": reason},
        [Notice(uid, f"Your shop is suspended: {reason}", "/seller") for uid in vendor_staff_ids(db, vendor.id)],
    )
    ctx.commit()
    return vendor_out(db, vendor, staff_view=True)


def reinstate(ctx: Ctx, vendor_id: str, reason: str) -> dict:
    db = ctx.db
    vendor = get_vendor(db, vendor_id)
    _move(ctx, vendor, "active", reason, "reinstate")
    emit(
        db,
        "vendor.reinstated",
        {"vendor_id": vendor.id},
        [Notice(uid, "Your shop is live again", "/seller") for uid in vendor_staff_ids(db, vendor.id)],
    )
    ctx.commit()
    return vendor_out(db, vendor, staff_view=True)


def assign_tier(ctx: Ctx, vendor_id: str, tier_id: str, reason: str) -> dict:
    db = ctx.db
    vendor = get_vendor(db, vendor_id)
    if db.get(CommissionTier, tier_id) is None:
        raise Unprocessable(f"Tier {tier_id} does not exist")
    before = vendor.tier_id
    vendor.tier_id = tier_id
    ctx.audit("vendor", "assign_tier", "vendor", vendor_id, before={"tier_id": before}, after={"tier_id": tier_id}, reason=reason)
    ctx.commit()
    db.expire(vendor)
    return vendor_out(db, get_vendor(db, vendor_id), staff_view=True)


def delete_vendor(ctx: Ctx, vendor_id: str) -> None:
    db = ctx.db
    vendor = get_vendor(db, vendor_id)
    if vendor.deleted_at:
        raise Conflict(f"{vendor.name} was already deleted", code="vendor_deleted")
    open_subs = db.scalars(
        select(SubOrder.id).where(SubOrder.vendor_id == vendor_id, SubOrder.status.in_(OPEN_SUB_ORDER))
    ).all()
    if open_subs:
        raise Conflict(
            f"{vendor.name} still has {len(open_subs)} open order(s). Finish or cancel them first.",
            code="vendor_has_open_orders",
            details={"sub_orders": list(open_subs)},
        )
    unpaid = db.scalars(select(Payout.id).where(Payout.vendor_id == vendor_id, Payout.status.in_(UNPAID_PAYOUT))).all()
    if unpaid:
        raise Conflict(
            f"{vendor.name} has payouts in progress ({', '.join(unpaid)}). Settle them first.",
            code="vendor_has_payouts",
        )
    vendor.deleted_at = utcnow()
    for product in db.scalars(select(Product).where(Product.vendor_id == vendor_id)).all():
        product.active = False
    staff = db.scalars(select(User).where(User.vendor_id == vendor_id)).all()
    for user in staff:
        user.vendor_id = None
        link = db.get(UserRole, {"user_id": user.id, "role_id": "vendor"})
        if link:
            db.delete(link)
    ctx.audit(
        "vendor",
        "delete",
        "vendor",
        vendor_id,
        before={"status": vendor.status, "staff": [u.id for u in staff]},
        after={"deleted_at": vendor.deleted_at, "products_hidden": True},
    )
    ctx.commit()


def _document(vendor: Vendor, doc_id: str) -> VendorDocument:
    doc = next((d for d in vendor.documents if d.id == doc_id), None)
    if doc is None:
        raise NotFound("Document", doc_id)
    return doc


def review_document(ctx: Ctx, vendor_id: str, doc_id: str, decision: str, reason: str | None) -> dict:
    db = ctx.db
    vendor = get_vendor(db, vendor_id)
    doc = _document(vendor, doc_id)
    if doc.status not in ("submitted", "verified", "rejected") or not doc.file_path:
        raise Conflict(f"{doc.name} has not been uploaded yet", code="document_missing")
    if decision == "rejected" and not reason:
        raise Unprocessable("Give a reason so the vendor knows what to fix", code="reason_required")
    before = doc.status
    doc.status = decision
    doc.reviewed_by = ctx.user_id
    doc.reviewed_at = utcnow()
    ctx.audit("vendor", "review_document", "vendor_document", doc.id, before={"status": before}, after={"status": decision, "vendor_id": vendor_id}, reason=reason)
    if decision == "rejected":
        emit(
            db,
            "vendor.document_rejected",
            {"vendor_id": vendor_id, "document": doc.id},
            [Notice(uid, f"{doc.name} was not accepted: {reason}", "/seller/storefront") for uid in vendor_staff_ids(db, vendor_id)],
        )
    ctx.commit()
    return vendor_out(db, vendor, staff_view=True)


def document_file(ctx: Ctx, vendor_id: str, doc_id: str):
    vendor = get_vendor(ctx.db, vendor_id)
    doc = _document(vendor, doc_id)
    ctx.audit("vendor", "view_document", "vendor_document", doc.id, after={"vendor_id": vendor_id, "kind": doc.kind})
    ctx.commit()
    return files.document_response(doc.file_path, doc.content_type, doc.original_filename)


# Vendor self-service -------------------------------------------------------------


def my_vendor(ctx: Ctx) -> Vendor:
    vendor = ctx.db.get(Vendor, ctx.vendor_id)
    if vendor is None or vendor.deleted_at:
        raise NotFound("Shop", ctx.vendor_id)
    return vendor


def my_shop(ctx: Ctx) -> dict:
    return vendor_out(ctx.db, my_vendor(ctx), staff_view=False)


def update_shop(ctx: Ctx, body) -> dict:
    vendor = my_vendor(ctx)
    before = snapshot(vendor, SHOP_EDITABLE)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(vendor, field, value)
    ctx.audit("vendor", "update_shop", "vendor", vendor.id, before=before, after=snapshot(vendor, SHOP_EDITABLE))
    ctx.commit()
    return vendor_out(ctx.db, vendor, staff_view=False)


def upload_shop_image(ctx: Ctx, upload: UploadFile) -> dict:
    vendor = my_vendor(ctx)
    before = vendor.image_url
    vendor.image_url = files.save_image(upload, "shops", vendor.id)
    ctx.audit("vendor", "upload_image", "vendor", vendor.id, before={"image_url": before}, after={"image_url": vendor.image_url})
    ctx.commit()
    return vendor_out(ctx.db, vendor, staff_view=False)


def _store_document(ctx: Ctx, vendor: Vendor, doc: VendorDocument, upload: UploadFile) -> None:
    before = doc.status
    path, content_type = files.save_document(upload, vendor.id, doc.id)
    doc.file_path = path
    doc.content_type = content_type
    doc.original_filename = (upload.filename or f"{doc.kind}")[:255]
    doc.uploaded_at = utcnow()
    doc.status = "submitted"
    doc.reviewed_by = None
    doc.reviewed_at = None
    ctx.audit("vendor", "upload_document", "vendor_document", doc.id, before={"status": before}, after={"status": "submitted", "vendor_id": vendor.id, "kind": doc.kind})


def upload_document(ctx: Ctx, doc_id: str, upload: UploadFile) -> dict:
    vendor = my_vendor(ctx)
    _store_document(ctx, vendor, _document(vendor, doc_id), upload)
    ctx.commit()
    return vendor_out(ctx.db, vendor, staff_view=False)


def my_document_file(ctx: Ctx, doc_id: str):
    vendor = my_vendor(ctx)
    doc = _document(vendor, doc_id)
    return files.document_response(doc.file_path, doc.content_type, doc.original_filename)


def submit_for_review(ctx: Ctx) -> dict:
    db = ctx.db
    vendor = my_vendor(ctx)
    missing = [d.name for d in vendor.documents if d.status in ("missing", "rejected")]
    if missing:
        raise Conflict(f"Upload these documents first: {', '.join(missing)}.", code="documents_missing", details={"documents": missing})
    _move(ctx, vendor, "under_review", "Documents submitted", "submit_application")
    _notify_reviewers(db, vendor)
    ctx.commit()
    return vendor_out(db, vendor, staff_view=False)


def apply(ctx: Ctx, *, name: str, country: str, city: str, headline: str, about: str, uploads: dict[str, UploadFile | None]) -> Vendor:
    """'Sell on Bazaar': a signed-in customer opens a shop. It goes live after verification."""
    db = ctx.db
    user = ctx.user
    if user.vendor_id:
        raise Conflict("You already run a shop. Open Seller Central instead.", code="already_vendor")
    with system_scope(db):
        vendor = Vendor(
            id=new_id("V", 6),
            name=name.strip(),
            slug=_unique_slug(db, name),
            country=country.upper(),
            city=city,
            headline=headline,
            about=about,
            status="draft",
            tier_id="starter",
            warehouse_id=WAREHOUSE_BY_COUNTRY.get(country.upper(), "WH-EAST"),
            hue=sum(map(ord, name)) % 360,
            since=utcnow().date(),
        )
        db.add(vendor)
        db.flush()
        docs = _new_documents(db, vendor.id)
        _event(db, vendor, None, "draft", user.id, "Application started")
        _attach_owner(db, user, vendor.id, user.id)
        db.flush()
        for doc in docs:
            upload = uploads.get(doc.kind)
            if upload is not None and upload.filename:
                _store_document(ctx, vendor, doc, upload)
        ready = all(d.status == "submitted" for d in docs)
        if ready:
            vendor.status = "under_review"
            _event(db, vendor, "draft", "under_review", user.id, "Documents submitted")
            _notify_reviewers(db, vendor)
        ctx.audit(
            "vendor",
            "submit_application",
            "vendor",
            vendor.id,
            before=None,
            after={"name": vendor.name, "status": vendor.status, "documents": {d.kind: d.status for d in docs}},
        )
    ctx.commit()
    db.expire_all()
    return vendor
