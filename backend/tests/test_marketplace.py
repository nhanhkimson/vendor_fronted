"""Research section 10, gates G1–G5, Appendix B (corrected) and Appendix C."""

from datetime import UTC, datetime, timedelta
from threading import Barrier, Thread

import pytest
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from app.core.db import owner_engine
from app.core.security import hash_password
from app.domain.money import commission_fee
from app.domain.pricing import CouponTerms, QuoteLine, build_quote
from tests.conftest import available, call, clear_cart, expect

SHIP = {"ship_name": "Maya R.", "ship_address": "St. 240, Daun Penh, Phnom Penh"}
CARD = {"card_number": "4242 4242 4242 4242"}


def _buy(client, token, variant_id: str, coupon: str | None = None) -> dict:
    clear_cart(client, token)
    call(client, "POST", "/api/cart/items", token, {"variant_id": variant_id, "qty": 1})
    if coupon:
        call(client, "POST", "/api/cart/coupon", token, {"code": coupon})
    intent = call(client, "POST", "/api/checkout", token, SHIP, ok=201)
    return call(client, "POST", f"/api/payments/{intent['id']}/confirm", token, CARD)


def _line(vendor: str, price: int) -> QuoteLine:
    return QuoteLine(
        variant_id="v",
        product_id="p",
        vendor_id=vendor,
        title="Item",
        sku="SKU",
        size="One size",
        color="Natural",
        unit_price_cents=price,
        qty=1,
    )


def test_appendix_b_customer_pays_90_and_commission_base_stays_full():
    """Corrected Appendix B, in cents.

    The research table says the customer pays $100 and Vendor A's commission
    base falls to $50. A platform-funded $10 coupon means the customer pays
    $90, and Vendor A's commission base stays the full $60 item.
    """
    coupon = CouponTerms("APPENDIX", "platform", "VA", "fixed", None, 1000, 0, "Vendor A")
    quote = build_quote(
        [_line("VA", 6000), _line("VB", 3000)],
        {"VA": ("Vendor A", 500), "VB": ("Vendor B", 500)},
        coupon,
    )
    groups = {group.vendor_id: group for group in quote.groups}
    assert quote.total_cents == 9000
    assert groups["VA"].platform_discount_cents == 1000
    assert groups["VA"].vendor_discount_cents == 0
    assert groups["VB"].platform_discount_cents == 0
    assert groups["VA"].lines[0].commission_base_cents == 6000
    assert groups["VB"].lines[0].commission_base_cents == 3000
    fee_a = commission_fee(6000, 1500, 0)
    fee_b = commission_fee(3000, 1200, 0)
    assert fee_a == 900
    assert fee_b == 360
    net_a = 6000 + 500 - fee_a
    net_b = 3000 + 500 - fee_b
    assert net_a == 5600
    assert net_b == 3140
    assert net_a + fee_a == groups["VA"].charged_cents + groups["VA"].platform_discount_cents
    assert net_b + fee_b == groups["VB"].charged_cents + groups["VB"].platform_discount_cents


def test_platform_coupon_does_not_shrink_the_frozen_commission_base(client, tokens):
    placed = _buy(client, tokens["maya"], "P04-1", coupon="WELCOME10")
    order = call(client, "GET", f"/api/orders/{placed['id']}", tokens["ava"])
    sub = next(item for item in order["sub_orders"] if item["vendor_id"] == "V03")
    assert sub["items_subtotal_cents"] == 4800
    assert sub["platform_discount_cents"] == 480
    assert sub["charged_cents"] == 4800 + 650 - 480
    assert sub["vendor_net_cents"] + sub["commission_cents"] == sub["charged_cents"] + sub["platform_discount_cents"]
    lines = call(client, "GET", "/api/commission-lines?vendor_id=V03", tokens["ava"])
    frozen = next(line for line in lines if line["order_id"] == order["id"])
    assert frozen["base_cents"] == 4800
    assert frozen["base_cents"] != sub["items_subtotal_cents"] - sub["platform_discount_cents"]


def test_g1_support_cannot_change_rules_and_admin_action_is_audited(client, tokens):
    expect(
        client,
        "POST",
        "/api/commission-rules/CR-GROW/revise",
        tokens["lin"],
        403,
        "permission_denied",
        {"rate_bps": 1000, "min_fee_cents": 30},
    )
    try:
        call(client, "PATCH", "/api/customers/theo", tokens["ava"], {"city": "Porto"})
        page = call(client, "GET", "/api/audit-logs?actor=ava&action=update&resource=theo", tokens["ava"])
        row = next(item for item in page["items"] if item.get("after") and item["after"].get("city") == "Porto")
        assert row["outcome"] == "success"
        assert "admin" in row["actor_roles"]
        assert row["before"]["city"] == "Lisbon"
        assert row["after"]["city"] == "Porto"
    finally:
        call(client, "PATCH", "/api/customers/theo", tokens["ava"], {"city": "Lisbon"})


def test_g2_and_section10_vendor_isolation_is_404_and_rls(client, tokens, as_app):
    hidden = expect(client, "GET", "/api/seller/products/P10", tokens["kein"], 404, "not_found")
    assert "P10" in hidden["detail"]
    expect(client, "GET", "/api/seller/orders/O-1001-V06", tokens["kein"], 404, "not_found")
    expect(client, "GET", "/api/seller/payouts/PAY-06", tokens["kein"], 404, "not_found")
    own = call(client, "GET", "/api/seller/products/P08", tokens["kein"])
    assert own["vendor_id"] == "V04"

    visible = {row[0] for row in as_app("vendor", "SELECT id FROM products", user_id="kein", vendor_id="V04")}
    assert "P08" in visible
    assert "P10" not in visible
    payouts = as_app("vendor", "SELECT id FROM payouts WHERE id = 'PAY-06'", user_id="kein", vendor_id="V04")
    assert payouts == []
    own_payouts = as_app("vendor", "SELECT id FROM payouts WHERE id = 'PAY-04'", user_id="kein", vendor_id="V04")
    assert own_payouts

    call(client, "GET", "/api/cart", tokens["maya"])
    theo_carts = as_app("customer", "SELECT user_id FROM carts", user_id="theo")
    assert all(row[0] == "theo" for row in theo_carts)
    maya_saved = {row[0] for row in as_app("customer", "SELECT product_id FROM wishlist_items", user_id="maya")}
    assert {"P05", "P09", "P17"} <= maya_saved
    theo_saved = as_app("customer", "SELECT product_id FROM wishlist_items", user_id="theo")
    assert theo_saved == []

    denied = call(client, "GET", "/api/audit-logs?actor=kein&outcome=denied&resource=P10", tokens["lin"])
    assert any(item["outcome"] == "denied" and item["resource_id"] == "P10" for item in denied["items"])


def test_g3_one_payment_two_suborders_and_two_tracking_numbers(client, tokens):
    clear_cart(client, tokens["maya"])
    call(client, "POST", "/api/cart/items", tokens["maya"], {"variant_id": "P12-1", "qty": 1})
    call(client, "POST", "/api/cart/items", tokens["maya"], {"variant_id": "P08-1", "qty": 1})
    intent = call(client, "POST", "/api/checkout", tokens["maya"], SHIP, ok=201)
    order = call(client, "POST", f"/api/payments/{intent['id']}/confirm", tokens["maya"], CARD)
    assert len(order["sub_orders"]) == 2
    assert {sub["vendor_id"] for sub in order["sub_orders"]} == {"V06", "V04"}
    anne = next(sub for sub in order["sub_orders"] if sub["vendor_id"] == "V06")
    kein = next(sub for sub in order["sub_orders"] if sub["vendor_id"] == "V04")

    call(client, "POST", f"/api/seller/orders/{anne['id']}/accept", tokens["jess"])
    call(client, "POST", f"/api/seller/orders/{anne['id']}/pack", tokens["jess"])
    shipped = call(
        client,
        "POST",
        f"/api/seller/orders/{anne['id']}/ship",
        tokens["jess"],
        {"tracking_number": "US-ANNE-1", "carrier": "USPS"},
    )
    assert shipped["tracking_number"] == "US-ANNE-1"
    parent = call(client, "GET", f"/api/account/orders/{order['id']}", tokens["maya"])
    assert parent["status"] == "partially_fulfilled"

    call(client, "POST", f"/api/seller/orders/{kein['id']}/accept", tokens["kein"])
    call(client, "POST", f"/api/seller/orders/{kein['id']}/pack", tokens["kein"])
    call(
        client,
        "POST",
        f"/api/seller/orders/{kein['id']}/ship",
        tokens["kein"],
        {"tracking_number": "US-KEIN-1", "carrier": "USPS"},
    )
    parent = call(client, "GET", f"/api/account/orders/{order['id']}", tokens["maya"])
    tracking = {sub["tracking_number"] for sub in parent["sub_orders"]}
    assert tracking == {"US-ANNE-1", "US-KEIN-1"}
    assert parent["status"] == "fulfilled"


def test_g4_changing_the_rate_does_not_rewrite_history(client, tokens):
    order = _buy(client, tokens["maya"], "P03-blush")
    lines = call(client, "GET", "/api/commission-lines?vendor_id=V02", tokens["ava"])
    frozen = next(line for line in lines if line["order_id"] == order["id"])
    assert frozen["rule_id"] == "CR-START"
    assert frozen["rate_bps"] == 1500
    assert frozen["rule_version"] == 1
    revised = None
    restored = None
    try:
        revised = call(
            client,
            "POST",
            "/api/commission-rules/CR-START/revise",
            tokens["ava"],
            {"rate_bps": 1000, "min_fee_cents": 30, "name": "Starter tier"},
        )
        assert revised["version"] == 2 and revised["open"] and revised["rate_bps"] == 1000
        again = call(client, "GET", "/api/commission-lines?vendor_id=V02", tokens["ava"])
        still = next(line for line in again if line["id"] == frozen["id"])
        assert still["rate_bps"] == 1500 and still["rule_version"] == 1 and still["rule_id"] == "CR-START"
        rules = call(client, "GET", "/api/commission-rules?include_ended=true", tokens["ava"])
        old = next(rule for rule in rules if rule["id"] == "CR-START")
        assert old["effective_to"] and not old["open"]
        open_starter = [rule for rule in rules if rule["target_type"] == "tier" and rule["target_id"] == "starter" and rule["open"]]
        assert len(open_starter) == 1
    finally:
        if revised:
            restored = call(
                client,
                "POST",
                f"/api/commission-rules/{revised['id']}/revise",
                tokens["ava"],
                {"rate_bps": 1500, "min_fee_cents": 30, "name": "Starter tier"},
            )
            assert restored["rate_bps"] == 1500 and restored["open"]


def test_g5_seeded_demo_ledger_and_sub_orders_balance(client, tokens, as_app):
    trial = call(client, "GET", "/api/ledger/trial-balance", tokens["ava"])
    assert trial["balanced"] is True
    assert sum(row["debit_cents"] for row in trial["rows"]) == sum(row["credit_cents"] for row in trial["rows"])
    broken = as_app(
        "platform",
        "SELECT id FROM sub_orders "
        "WHERE vendor_net_cents + commission_cents <> charged_cents + platform_discount_cents",
        user_id="ava",
    )
    assert broken == []
    journals = as_app(
        "platform",
        "SELECT journal_id FROM ledger_entries GROUP BY journal_id "
        "HAVING SUM(debit_cents) <> SUM(credit_cents)",
        user_id="ava",
    )
    assert journals == []


def test_section10_audit_records_role_at_the_time_and_sql_cannot_change_the_log(client, tokens, app_engine):
    original = call(client, "GET", "/api/seller/products/P10", tokens["jess"])["title"]
    try:
        call(client, "PATCH", "/api/seller/products/P10", tokens["jess"], {"title": "Wool felt coasters, audited"})
        page = call(client, "GET", "/api/audit-logs?actor=jess&module=product&action=update&resource=P10", tokens["ava"])
        row = next(item for item in page["items"] if item["after"] and item["after"].get("title") == "Wool felt coasters, audited")
        assert row["before"]["title"] == original
        assert "vendor" in row["actor_roles"]
        assert row["actor_id"] == "jess"
        exported = client.get("/api/audit-logs/export?format=json&resource=P10", headers={"Authorization": f"Bearer {tokens['ava']}"})
        assert exported.status_code == 200, exported.text
        assert "Wool felt coasters, audited" in exported.text
    finally:
        call(client, "PATCH", "/api/seller/products/P10", tokens["jess"], {"title": original})

    for statement in (
        "UPDATE audit_logs SET reason = 'tamper'",
        "DELETE FROM audit_logs",
        "UPDATE commission_lines SET fee_cents = 0",
    ):
        with pytest.raises(ProgrammingError) as caught:
            with app_engine.begin() as conn:
                conn.execute(text(statement))
        assert "permission denied" in str(caught.value).lower()

    with app_engine.connect() as conn:
        before = conn.scalar(text("SELECT count(*) FROM audit_logs"))
        conn.rollback()
        trans = conn.begin()
        moved = conn.scalar(text("SELECT archive_audit_logs()"))
        assert int(moved) == int(before)
        trans.rollback()
    with app_engine.connect() as conn:
        after = conn.scalar(text("SELECT count(*) FROM audit_logs"))
        assert int(after) == int(before)
    expect(client, "POST", "/api/audit-logs/archive", tokens["ava"], 403, "permission_denied")
    expect(client, "POST", "/api/audit-logs/archive", tokens["lin"], 403, "permission_denied")


def test_section10_payout_needs_two_people_and_an_open_dispute_blocks_it(client, tokens):
    with owner_engine().connect() as conn:
        exists = conn.scalar(text("SELECT 1 FROM users WHERE id = 'sunday'"))
        if not exists:
            conn.execute(
                text(
                    "INSERT INTO users (id, email, password_hash, name, city, source, vendor_id, is_active, created_at) "
                    "VALUES ('sunday', 'sunday@firstsunday.local', :password, 'Sunday V.', 'United States', 'organic', 'V07', true, now())"
                ),
                {"password": hash_password("demo")},
            )
            conn.execute(
                text(
                    "INSERT INTO user_roles (user_id, role_id, assigned_by, assigned_at) "
                    "VALUES ('sunday', 'vendor', 'system', now())"
                )
            )
            conn.commit()
    login = client.post("/api/auth/token", data={"username": "sunday@firstsunday.local", "password": "demo"})
    assert login.status_code == 200, login.text
    sunday = login.json()["access_token"]

    requested = call(client, "POST", "/api/seller/payouts/PAY-06/request", tokens["jess"])
    assert requested["status"] == "requested"
    expect(client, "POST", "/api/payouts/PAY-06/approve", tokens["jess"], 403, "permission_denied", {"note": "Seller"})
    first = call(client, "POST", "/api/payouts/PAY-06/approve", tokens["daniel"], {"note": "First signature"})
    assert first["status"] == "pending_second_approval"
    expect(client, "POST", "/api/payouts/PAY-06/approve", tokens["daniel"], 409, "already_signed", {"note": "Again"})
    second = call(client, "POST", "/api/payouts/PAY-06/approve", tokens["lin"], {"note": "Second signature"})
    assert second["status"] == "approved"
    assert {item["approver_id"] for item in second["approvals"]} == {"daniel", "lin"}
    assert "jess" not in {item["approver_id"] for item in second["approvals"]}
    paid = call(client, "POST", "/api/payouts/PAY-06/pay", tokens["daniel"], {"reference": "TRF-1008"})
    assert paid["status"] == "paid" and paid["reference"] == "TRF-1008"
    trial = call(client, "GET", "/api/ledger/trial-balance", tokens["daniel"])
    assert trial["balanced"] is True

    expect(client, "POST", "/api/seller/payouts/PAY-07/request", sunday, 409, "dispute_open")
    assert call(client, "GET", "/api/payouts/PAY-07", tokens["ava"])["status"] == "held_for_dispute"
    matured = call(client, "POST", "/api/seller/payouts", tokens["jess"], ok=201)
    assert matured["status"] == "requested" and matured["amount_cents"] > 0
    expect(client, "POST", "/api/commission-rules/CR-PLAT/end", tokens["ava"], 409, "platform_rule", {"reason": "Cannot remove the fallback"})


def test_last_super_admin_and_support_cannot_promote_themselves(client, tokens):
    expect(client, "PUT", "/api/users/daniel/roles", tokens["daniel"], 409, "last_super_admin", {"role_ids": ["admin"]})
    expect(client, "PUT", "/api/users/lin/roles", tokens["lin"], 403, "permission_denied", {"role_ids": ["super_admin"]})
    daniel = call(client, "GET", "/api/users?q=daniel", tokens["ava"])
    account = next(user for user in daniel if user["id"] == "daniel")
    assert any(role["id"] == "super_admin" for role in account["roles"])


def test_revoke_permission_takes_effect_on_the_next_request(client, tokens):
    created = call(
        client,
        "POST",
        "/api/roles",
        tokens["daniel"],
        {"name": "Finance Clerk", "kind": "platform", "permissions": ["report:read", "payout:read"]},
        ok=201,
    )
    assert "report:read" in created["direct"]
    narrowed = call(client, "DELETE", f"/api/roles/{created['id']}/permissions/report:read", tokens["daniel"])
    assert "report:read" not in narrowed["direct"]
    call(client, "DELETE", f"/api/roles/{created['id']}", tokens["daniel"])

    call(client, "DELETE", "/api/roles/vendor/permissions/product:delete", tokens["daniel"])
    try:
        expect(client, "DELETE", "/api/seller/products/P12", tokens["jess"], 403, "permission_denied")
    finally:
        restored = call(client, "POST", "/api/roles/vendor/permissions/product:delete", tokens["daniel"])
        assert "product:delete" in restored["direct"]


def test_state_machines_reject_skipped_steps(client, tokens):
    expect(
        client,
        "POST",
        "/api/seller/orders/O-1001-V06/deliver",
        tokens["jess"],
        409,
        "invalid_transition",
    )
    expect(
        client,
        "POST",
        "/api/seller/orders/O-1001-V06/ship",
        tokens["jess"],
        409,
        "tracking_required",
        {"tracking_number": "   "},
    )
    assert call(client, "GET", "/api/seller/orders/O-1001-V06", tokens["jess"])["status"] == "packing"
    expect(
        client,
        "POST",
        "/api/orders/sub-orders/O-1006-V01/status",
        tokens["ava"],
        409,
        "invalid_transition",
        {"status": "delivered", "note": "Skip ahead"},
    )
    assert call(client, "GET", "/api/orders/O-1006", tokens["ava"])["sub_orders"][0]["status"] == "accepted"


def test_two_buyers_cannot_both_take_the_last_unit(client, tokens):
    product = call(
        client,
        "POST",
        "/api/seller/products",
        tokens["jess"],
        {
            "title": "Last unit race scarf",
            "description": "One left",
            "price_cents": 2500,
            "category_id": "c2a",
            "low_stock_threshold": 0,
            "variants": [{"sku": "RACE-1", "size": "One size", "color": "Natural", "stock": 1}],
        },
        ok=201,
    )
    variant_id = product["variants"][0]["id"]
    for token in (tokens["maya"], tokens["theo"]):
        clear_cart(client, token)
        call(client, "POST", "/api/cart/items", token, {"variant_id": variant_id, "qty": 1})
    winner = call(client, "POST", "/api/checkout", tokens["maya"], SHIP, ok=201)
    blocked = expect(client, "POST", "/api/checkout", tokens["theo"], 409, "cart_problems", SHIP)
    assert "Sold out" in blocked["detail"]
    order = call(client, "POST", f"/api/payments/{winner['id']}/confirm", tokens["maya"], CARD)
    assert order["id"]
    assert available(client, product["id"], variant_id) == 0


def test_concurrent_checkout_lets_only_one_reservation_succeed(client, tokens):
    """Both buyers pass the quote together; the conditional stock update admits one."""
    from fastapi.testclient import TestClient

    from app.main import app
    from tests.conftest import auth

    product = call(
        client,
        "POST",
        "/api/seller/products",
        tokens["jess"],
        {
            "title": "Concurrent last unit",
            "description": "Race",
            "price_cents": 1800,
            "category_id": "c2a",
            "low_stock_threshold": 0,
            "variants": [{"sku": "RACE-2", "size": "One size", "color": "Natural", "stock": 1}],
        },
        ok=201,
    )
    variant_id = product["variants"][0]["id"]
    for token in (tokens["maya"], tokens["theo"]):
        clear_cart(client, token)
        call(client, "POST", "/api/cart/items", token, {"variant_id": variant_id, "qty": 1})

    barrier = Barrier(2)
    results: dict[str, int] = {}

    def race(name: str, token: str) -> None:
        barrier.wait(timeout=5)
        with TestClient(app) as local:
            response = local.post("/api/checkout", headers=auth(token), json=SHIP)
            results[name] = response.status_code

    threads = [Thread(target=race, args=("maya", tokens["maya"])), Thread(target=race, args=("theo", tokens["theo"]))]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sorted(results.values()) == [201, 409]


def test_declined_card_releases_the_reserved_stock(client, tokens):
    before = available(client, "P09", "P09-1")
    clear_cart(client, tokens["maya"])
    call(client, "POST", "/api/cart/items", tokens["maya"], {"variant_id": "P09-1", "qty": 1})
    intent = call(client, "POST", "/api/checkout", tokens["maya"], SHIP, ok=201)
    assert available(client, "P09", "P09-1") == before - 1
    expect(
        client,
        "POST",
        f"/api/payments/{intent['id']}/confirm",
        tokens["maya"],
        402,
        "payment_declined",
        {"card_number": "4000 0000 0000 0002"},
    )
    assert available(client, "P09", "P09-1") == before


def test_confirming_a_payment_twice_creates_one_order(client, tokens):
    before = available(client, "P02", "P02-1")
    clear_cart(client, tokens["maya"])
    call(client, "POST", "/api/cart/items", tokens["maya"], {"variant_id": "P02-1", "qty": 1})
    intent = call(client, "POST", "/api/checkout", tokens["maya"], SHIP, ok=201)
    first = call(client, "POST", f"/api/payments/{intent['id']}/confirm", tokens["maya"], CARD)
    second = call(client, "POST", f"/api/payments/{intent['id']}/confirm", tokens["maya"], CARD)
    assert first["id"] == second["id"]
    assert available(client, "P02", "P02-1") == before - 1


def test_coupon_limits_and_verified_purchase_reviews(client, tokens):
    clear_cart(client, tokens["theo"])
    call(client, "POST", "/api/cart/items", tokens["theo"], {"variant_id": "P08-1", "qty": 1})
    rejected = expect(client, "POST", "/api/cart/coupon", tokens["theo"], 422, "coupon_rejected", {"code": "WELCOME10"})
    assert "WELCOME10" in rejected["detail"]
    expect(client, "DELETE", "/api/coupons/WELCOME10", tokens["ava"], 409, "coupon_used")
    now = datetime.now(UTC)
    expect(
        client,
        "POST",
        "/api/coupons",
        tokens["ava"],
        422,
        "flash_window",
        {
            "code": "FLASHLONG",
            "funded_by": "platform",
            "discount_type": "percent",
            "percent_off": 10,
            "starts_at": now.isoformat(),
            "ends_at": (now + timedelta(days=30)).isoformat(),
            "is_flash": True,
            "note": "Too long for a flash window",
        },
    )

    expect(
        client,
        "POST",
        "/api/account/reviews",
        tokens["maya"],
        409,
        "not_delivered",
        {"sub_order_id": "O-1001-V06", "product_id": "P10", "rating": 4, "body": "Still waiting for this to arrive."},
    )
    review = call(
        client,
        "POST",
        "/api/account/reviews",
        tokens["maya"],
        {"sub_order_id": "O-1003-V09", "product_id": "P16", "rating": 5, "body": "The bud vase arrived safely and the glaze is lovely."},
        ok=201,
    )
    assert review["verified_purchase"] is True
    expect(
        client,
        "POST",
        "/api/account/reviews",
        tokens["maya"],
        409,
        "already_reviewed",
        {"sub_order_id": "O-1003-V09", "product_id": "P16", "rating": 4, "body": "Trying to review the same vase again."},
    )
    replied = call(client, "POST", "/api/seller/reviews/R04/reply", tokens["jess"], {"response": "Thank you, the stars stay yours."})
    assert replied["rating"] == 5


def test_low_stock_notification_and_vendor_csv_is_only_their_shop(client, tokens):
    call(client, "POST", "/api/seller/inventory/P12-1/adjust", tokens["jess"], {"set_to": 2, "reason": "Count for the low-stock test"})
    try:
        notes = call(client, "GET", "/api/notifications", tokens["jess"])
        assert any(item["kind"] == "stock.low" and "down to 2" in item["title"] for item in notes["items"])
    finally:
        call(client, "POST", "/api/seller/inventory/P12-1/adjust", tokens["jess"], {"set_to": 15, "reason": "Put the demo stock back"})

    overview = call(client, "GET", "/api/seller/reports/overview", tokens["jess"])
    assert overview["vendor_id"] == "V06"
    assert {row["vendor_id"] for row in overview["sales_by_vendor"]} == {"V06"}
    staff = call(client, "GET", "/api/reports/overview", tokens["ava"])
    assert len({row["vendor_id"] for row in staff["sales_by_vendor"]}) > 1
    exported = call(client, "GET", "/api/seller/reports/sales/export", tokens["jess"])
    assert "text/csv" in exported.headers["content-type"]
    vendors = {line.split(",")[0] for line in exported.text.splitlines()[1:] if line.strip()}
    assert vendors == {"V06"}


def test_money_identity_holds_after_the_suite(as_app):
    broken = as_app(
        "platform",
        "SELECT id FROM sub_orders "
        "WHERE vendor_net_cents + commission_cents <> charged_cents + platform_discount_cents",
        user_id="ava",
    )
    assert broken == []
    unbalanced = as_app(
        "platform",
        "SELECT COALESCE(SUM(debit_cents), 0), COALESCE(SUM(credit_cents), 0) FROM ledger_entries",
        user_id="ava",
    )
    assert unbalanced[0][0] == unbalanced[0][1]
