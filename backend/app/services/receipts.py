"""E-receipt emails after a successful payment."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.util import money
from app.models.identity import User
from app.models.order import Order
from app.models.vendor import Vendor
from app.services.mail import send_mail


def send_order_receipt(db: Session, order: Order, buyer: User) -> str | None:
    if not buyer.email:
        return None
    lines: list[str] = []
    html_rows: list[str] = []
    for sub in order.sub_orders:
        vendor = db.get(Vendor, sub.vendor_id)
        shop = vendor.name if vendor else sub.vendor_id
        lines.append(f"  Shop: {shop}")
        html_rows.append(f'<tr><td colspan="2" style="padding:12px 0 4px;font-weight:600">{shop}</td></tr>')
        for line in sub.lines:
            title = line.title or line.product_id
            row = f"    {line.qty} × {title} — {money(line.line_total_cents)}"
            lines.append(row)
            html_rows.append(
                f"<tr><td style='padding:4px 0;color:#6b6258'>{line.qty} × {title}</td>"
                f"<td style='padding:4px 0;text-align:right'>{money(line.line_total_cents)}</td></tr>"
            )
        lines.append("")

    discount = f"Discount: −{money(order.discount_cents)}\n" if order.discount_cents else ""
    text = (
        f"Hi {buyer.name},\n\n"
        f"Payment received for order {order.id}.\n\n"
        f"Ship to: {order.ship_name}\n{order.ship_address}\n\n"
        "Items\n"
        + "\n".join(lines)
        + f"\nSubtotal: {money(order.items_subtotal_cents)}\n"
        f"Shipping: {money(order.shipping_cents)}\n"
        f"{discount}"
        f"Total paid: {money(order.total_cents)}\n"
        f"Card: •••• {order.card_last4 or '****'}\n\n"
        f"Track your parcel: /account/orders/{order.id}\n\n"
        "Thank you for shopping on Bazaar.\n"
    )
    html = f"""
    <div style="font-family:Georgia,serif;max-width:560px;margin:0 auto;color:#171411">
      <p style="font-size:28px;margin:0 0 4px">Bazaar</p>
      <p style="color:#6b6258;margin:0 0 24px">E-receipt</p>
      <p>Hi {buyer.name},</p>
      <p>Payment received for <strong>{order.id}</strong>.</p>
      <p style="color:#6b6258">Ship to {order.ship_name}<br/>{order.ship_address}</p>
      <table style="width:100%;border-collapse:collapse;margin:24px 0">{"".join(html_rows)}</table>
      <p style="margin:0">Items {money(order.items_subtotal_cents)}</p>
      <p style="margin:0">Shipping {money(order.shipping_cents)}</p>
      {"<p style='margin:0;color:#b8572a'>Discount −" + money(order.discount_cents) + "</p>" if order.discount_cents else ""}
      <p style="font-size:22px;margin:16px 0">Total paid {money(order.total_cents)}</p>
      <p style="color:#6b6258">Card •••• {order.card_last4 or "****"}</p>
      <p><a href="/account/orders/{order.id}">Track your order</a></p>
    </div>
    """
    return send_mail(
        to=buyer.email,
        subject=f"Bazaar receipt · {order.id} · {money(order.total_cents)}",
        text=text,
        html=html,
    )
