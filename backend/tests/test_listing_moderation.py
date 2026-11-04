"""Product listing maker-checker: submit → approve/reject; storefront shows published only."""

from tests.conftest import call, expect


def test_listing_submit_approve_and_storefront_visibility(client, tokens):
    created = call(
        client,
        "POST",
        "/api/seller/products",
        tokens["jess"],
        {
            "title": "Maker-checker demo scarf",
            "description": "Needs staff approval before it is public.",
            "price_cents": 1800,
            "category_id": "c2a",
            "variants": [{"sku": "P-MC-SCARF", "size": "One size", "color": "Natural", "stock": 4}],
        },
        ok=201,
    )
    assert created["listing_status"] == "draft"
    assert created["active"] is False

    pending = call(client, "POST", f"/api/seller/products/{created['id']}/submit", tokens["jess"])
    assert pending["listing_status"] == "pending_review"

    queue = call(client, "GET", "/api/listings/pending", tokens["ava"])
    assert any(item["id"] == created["id"] for item in queue)

    published = call(client, "POST", f"/api/listings/{created['id']}/approve", tokens["ava"])
    assert published["listing_status"] == "published"
    assert published["active"] is True

    store = call(client, "GET", f"/api/store/products/{created['id']}")
    assert store["id"] == created["id"]


def test_listing_reject_keeps_product_off_storefront(client, tokens):
    created = call(
        client,
        "POST",
        "/api/seller/products",
        tokens["jess"],
        {
            "title": "Rejected demo wrap",
            "description": "Will be rejected by support.",
            "price_cents": 2200,
            "category_id": "c2a",
            "variants": [{"sku": "P-MC-WRAP", "size": "One size", "color": "Charcoal", "stock": 2}],
        },
        ok=201,
    )
    call(client, "POST", f"/api/seller/products/{created['id']}/submit", tokens["jess"])
    rejected = call(
        client,
        "POST",
        f"/api/listings/{created['id']}/reject",
        tokens["lin"],
        {"reason": "Needs clearer photos and materials"},
    )
    assert rejected["listing_status"] == "rejected"
    assert rejected["active"] is False
    expect(client, "GET", f"/api/store/products/{created['id']}", tokens["maya"], 404, "not_found")


def test_seed_pending_listing_is_in_staff_queue(client, tokens):
    queue = call(client, "GET", "/api/listings/pending", tokens["ava"])
    assert any(item["id"] == "P19" for item in queue)
    expect(client, "GET", "/api/store/products/P19", tokens["maya"], 404, "not_found")
