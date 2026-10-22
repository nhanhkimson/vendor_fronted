"""M8 reviews: verified purchase only, moderation, and a vendor reply that cannot touch the stars."""

from decimal import Decimal

from sqlalchemy import select

from app.core.db import utcnow
from app.core.deps import Ctx
from app.core.errors import Conflict
from app.core.util import new_id
from app.domain.states import REVIEW
from app.models import Product, Review, ReviewEvent
from app.services.events import Notice, emit, vendor_staff_ids
from app.services.fulfilment import customer_sub_order
from app.services.present import review_cards
from app.services.tenancy import owned


def _rating(value: float) -> Decimal:
    steps = round(value * 2) / 2
    if steps < 1 or steps > 5:
        raise Conflict("Rating must be between 1 and 5, in half stars", code="bad_rating")
    return Decimal(str(steps))


def _sentiment(rating: Decimal) -> str:
    if rating >= 4:
        return "positive"
    if rating >= 3:
        return "neutral"
    return "negative"


_MODERATION = {
    "published": ["flag", "remove"],
    "flagged": ["restore", "remove"],
    "removed": ["restore"],
}


def _actions(ctx: Ctx, review: Review) -> list[str]:
    actions = []
    if ctx.scope == "platform" and ctx.can("review:moderate"):
        actions += _MODERATION.get(review.status, [])
    if ctx.scope == "vendor" and ctx.can("review:respond") and review.status != "removed":
        actions.append("respond")
    return actions


def review_out(ctx: Ctx, review: Review) -> dict:
    card = review_cards(ctx.db, [review])[0]
    card["buyer_id"] = review.buyer_id
    card["allowed_actions"] = _actions(ctx, review)
    return card


def list_reviews(ctx: Ctx, status: str | None, vendor_id: str | None, product_id: str | None) -> list[dict]:
    query = select(Review).order_by(Review.created_at.desc())
    if ctx.scope == "vendor":
        query = query.where(Review.vendor_id == ctx.vendor_id)
    elif ctx.scope == "customer":
        query = query.where(Review.buyer_id == ctx.user_id)
    elif vendor_id:
        query = query.where(Review.vendor_id == vendor_id)
    if status:
        query = query.where(Review.status == status)
    if product_id:
        query = query.where(Review.product_id == product_id)
    reviews = ctx.db.scalars(query.limit(200)).all()
    cards = {c["id"]: c for c in review_cards(ctx.db, reviews)}
    rows = []
    for review in reviews:
        card = cards[review.id]
        card["buyer_id"] = review.buyer_id
        card["allowed_actions"] = _actions(ctx, review)
        rows.append(card)
    return rows


def create_review(ctx: Ctx, body) -> dict:
    db = ctx.db
    sub = customer_sub_order(ctx, body.sub_order_id)
    if sub.status != "delivered":
        raise Conflict("You can review an item once it has been delivered", code="not_delivered")
    line = next((item for item in sub.lines if item.product_id == body.product_id), None)
    if line is None:
        raise Conflict("That item is not part of this order", code="not_in_order")
    existing = db.scalar(
        select(Review.id).where(
            Review.buyer_id == ctx.user_id,
            Review.sub_order_id == sub.id,
            Review.product_id == body.product_id,
        )
    )
    if existing:
        raise Conflict("You already reviewed this item", code="already_reviewed")
    rating = _rating(body.rating)
    review = Review(
        id=new_id("R", 8),
        product_id=body.product_id,
        vendor_id=sub.vendor_id,
        buyer_id=ctx.user_id,
        sub_order_id=sub.id,
        rating=rating,
        body=body.body.strip(),
        sentiment=_sentiment(rating),
        source="bazaar",
        status="published",
        created_at=utcnow(),
    )
    db.add(review)
    db.flush()
    db.add(ReviewEvent(review_id=review.id, from_status=None, to_status="published", actor_id=ctx.user_id, at=review.created_at))
    product = db.get(Product, body.product_id)
    ctx.audit(
        "customer",
        "create_review",
        "review",
        review.id,
        after={"product_id": review.product_id, "sub_order_id": sub.id, "rating": float(rating), "verified_purchase": True},
    )
    emit(
        db,
        "review.created",
        {"review_id": review.id, "product_id": review.product_id},
        [Notice(uid, f"New {rating}-star review of {product.title if product else body.product_id}", "/seller/reviews") for uid in vendor_staff_ids(db, sub.vendor_id)],
    )
    ctx.commit()
    return review_out(ctx, review)


def _moderate(ctx: Ctx, review_id: str, target: str, action: str, reason: str) -> dict:
    db = ctx.db
    review = db.get(Review, review_id)
    if review is None:
        from app.core.errors import NotFound

        raise NotFound("Review", review_id)
    before = review.status
    REVIEW.check(before, target, "Review")
    review.status = target
    review.moderation_reason = None if target == "published" else reason.strip()
    db.add(ReviewEvent(review_id=review.id, from_status=before, to_status=target, actor_id=ctx.user_id, reason=reason.strip(), at=utcnow()))
    ctx.audit("customer", action, "review", review.id, before={"status": before}, after={"status": target}, reason=reason)
    if target == "removed":
        emit(db, "review.removed", {"review_id": review.id}, [Notice(review.buyer_id, "A review you wrote was removed", f"/products/{review.product_id}", reason)])
    ctx.commit()
    return review_out(ctx, review)


def flag_review(ctx: Ctx, review_id: str, reason: str) -> dict:
    return _moderate(ctx, review_id, "flagged", "flag", reason)


def remove_review(ctx: Ctx, review_id: str, reason: str) -> dict:
    return _moderate(ctx, review_id, "removed", "remove", reason)


def restore_review(ctx: Ctx, review_id: str, reason: str) -> dict:
    return _moderate(ctx, review_id, "published", "restore", reason)


def respond(ctx: Ctx, review_id: str, response: str) -> dict:
    db = ctx.db
    review = owned(ctx, Review, review_id, "Review", "customer", "review")
    if review.status == "removed":
        raise Conflict("This review was removed, so it can't be replied to", code="review_removed")
    before = review.vendor_response
    review.vendor_response = response.strip()
    review.vendor_responded_at = utcnow()
    ctx.audit(
        "customer",
        "respond",
        "review",
        review.id,
        before={"vendor_response": before},
        after={"vendor_response": review.vendor_response, "rating_unchanged": float(review.rating) if review.rating is not None else None},
    )
    emit(
        db,
        "review.responded",
        {"review_id": review.id},
        [Notice(review.buyer_id, "The shop replied to your review", f"/products/{review.product_id}")],
    )
    ctx.commit()
    return review_out(ctx, review)
