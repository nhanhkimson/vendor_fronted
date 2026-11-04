"""Phase 5 gap coverage: maker-checker negatives, material re-review, archive, cancel/delivery, audit archive."""

from tests.conftest import call, clear_cart, expect

SHIP = {"ship_name": "Maya R.", "ship_address": "St. 240, Daun Penh, Phnom Penh"}
CARD = {"card_number": "4242 4242 4242 4242"}


def _create_draft(client, tokens, *, title: str, sku: str):
    return call(
        client,
        "POST",
        "/api/seller/products",
        tokens["jess"],
        {
            "title": title,
            "description": "Gap coverage product",
            "price_cents": 1900,
            "category_id": "c2a",
            "variants": [{"sku": sku, "size": "One size", "color": "Natural", "stock": 6}],
        },
        ok=201,
    )


def test_vendor_cannot_approve_or_reject_listing(client, tokens):
    created = _create_draft(client, tokens, title="Vendor cannot moderate", sku="GAP-MC-1")
    call(client, "POST", f"/api/seller/products/{created['id']}/submit", tokens["jess"])
    expect(client, "POST", f"/api/listings/{created['id']}/approve", tokens["jess"], 403, "permission_denied")
    expect(
        client,
        "POST",
        f"/api/listings/{created['id']}/reject",
        tokens["jess"],
        403,
        "permission_denied",
        {"reason": "Trying to self-approve"},
    )
    published = call(client, "POST", f"/api/listings/{created['id']}/approve", tokens["lin"])
    assert published["listing_status"] == "published"


def test_material_edit_republish_cycle(client, tokens):
    created = _create_draft(client, tokens, title="Material edit cycle", sku="GAP-MAT-1")
    call(client, "POST", f"/api/seller/products/{created['id']}/submit", tokens["jess"])
    call(client, "POST", f"/api/listings/{created['id']}/approve", tokens["ava"])

    edited = call(
        client,
        "PATCH",
        f"/api/seller/products/{created['id']}",
        tokens["jess"],
        {"title": "Material edit cycle (revised)", "price_cents": 2100},
    )
    assert edited["listing_status"] == "pending_review"
    expect(client, "GET", f"/api/store/products/{created['id']}", tokens["maya"], 404, "not_found")

    rejected = call(
        client,
        "POST",
        f"/api/listings/{created['id']}/reject",
        tokens["ava"],
        {"reason": "Price looks off for this category"},
    )
    assert rejected["listing_status"] == "rejected"

    pending = call(client, "POST", f"/api/seller/products/{created['id']}/submit", tokens["jess"])
    assert pending["listing_status"] == "pending_review"
    published = call(client, "POST", f"/api/listings/{created['id']}/approve", tokens["ava"])
    assert published["listing_status"] == "published"
    store = call(client, "GET", f"/api/store/products/{created['id']}")
    assert store["title"] == "Material edit cycle (revised)"


def test_seller_archive_and_restore(client, tokens):
    created = _create_draft(client, tokens, title="Archive restore scarf", sku="GAP-ARC-1")
    call(client, "POST", f"/api/seller/products/{created['id']}/submit", tokens["jess"])
    call(client, "POST", f"/api/listings/{created['id']}/approve", tokens["ava"])

    call(client, "DELETE", f"/api/seller/products/{created['id']}", tokens["jess"])
    expect(client, "GET", f"/api/store/products/{created['id']}", tokens["maya"], 404, "not_found")

    restored = call(client, "POST", f"/api/seller/products/{created['id']}/restore", tokens["jess"])
    assert restored["id"] == created["id"]
    assert restored["listing_status"] == "draft"
    assert restored.get("archived_at") is None


def test_customer_cancel_and_confirm_delivery(client, tokens):
    clear_cart(client, tokens["maya"])
    call(client, "POST", "/api/cart/items", tokens["maya"], {"variant_id": "P02-1", "qty": 1})
    intent = call(client, "POST", "/api/checkout", tokens["maya"], SHIP, ok=201)
    order = call(client, "POST", f"/api/payments/{intent['id']}/confirm", tokens["maya"], CARD)
    cancel_sub = order["sub_orders"][0]["id"]
    cancelled = call(
        client,
        "POST",
        f"/api/account/sub-orders/{cancel_sub}/cancel",
        tokens["maya"],
        {"reason": "Changed my mind"},
    )
    cancel_row = next(item for item in cancelled["sub_orders"] if item["id"] == cancel_sub)
    assert cancel_row["status"] == "cancelled"

    clear_cart(client, tokens["maya"])
    call(client, "POST", "/api/cart/items", tokens["maya"], {"variant_id": "P12-1", "qty": 1})
    intent = call(client, "POST", "/api/checkout", tokens["maya"], SHIP, ok=201)
    order = call(client, "POST", f"/api/payments/{intent['id']}/confirm", tokens["maya"], CARD)
    sub_id = order["sub_orders"][0]["id"]
    call(client, "POST", f"/api/seller/orders/{sub_id}/accept", tokens["jess"])
    call(client, "POST", f"/api/seller/orders/{sub_id}/pack", tokens["jess"])
    call(
        client,
        "POST",
        f"/api/seller/orders/{sub_id}/ship",
        tokens["jess"],
        {"tracking_number": "KH-GAP-DEL", "carrier": "Cambodia Post"},
    )
    delivered = call(client, "POST", f"/api/account/sub-orders/{sub_id}/confirm-delivery", tokens["maya"])
    # Endpoint returns the parent order; the sub-order should be delivered.
    sub = next(item for item in delivered["sub_orders"] if item["id"] == sub_id)
    assert sub["status"] == "delivered"


def test_super_admin_can_archive_audit_logs(client, tokens):
    result = call(client, "POST", "/api/audit-logs/archive", tokens["daniel"])
    assert "archived" in result
    assert result["archived"] >= 0
    page = call(client, "GET", "/api/audit-logs/archive", tokens["daniel"])
    assert "items" in page
