# Analysis review

The research document is the brief. These are the places it disagrees with itself, and what the build does instead.

## Appendix B charges the customer $100 after a $10 coupon

Vendor A is a $60 item plus $5 shipping. Vendor B is a $30 item plus $5 shipping. A $10 platform coupon comes off Vendor A's item. The customer pays **$90** (9000 cents), not $100.

## Appendix B also contradicts FR-9.4

The table reduces Vendor A's commission base to $50 because of the platform coupon. A platform-funded discount is paid by the platform. Vendor A's commission base stays the full **$60** item. At 15% the fee is $9.00, and the vendor net is $51 plus the $5 shipping that is not commissionable ($56). Vendor B at 12% is a $3.60 fee and a $31.40 net.

`test_appendix_b_customer_pays_90_and_commission_base_stays_full` reproduces those cents. `test_platform_coupon_does_not_shrink_the_frozen_commission_base` places a real order with WELCOME10 and checks the frozen base.

## Invariant 5 does not close when the platform funds a discount

`vendor_net + commission + processor_fee + refunds = captured_amount` cannot hold on a sub-order whose discount was paid by the platform, because the vendor is still owed the pre-discount amount. The identity used here is:

`vendor_net + commission = charged + platform_funded_discount`

Shipping is in both the charged amount and the vendor net, and it is not part of the commission base. There is no card processor fee in this demo.

## FR-2.5 and FR-2.6 cannot both be true of the app role

Clearing the hot audit log deletes rows. The app role may only insert and select. `archive_audit_logs()` is `SECURITY DEFINER`, Super Admin only at the API, and the call is audited. The app role's own `UPDATE` and `DELETE` are rejected by Postgres.

## The payout machine needs two signatures but only one approved state

The implemented machine is `eligible → requested → pending_second_approval → approved → paid`, plus `held_for_dispute`. The requester cannot sign. The same person cannot sign twice.

## `completed` had no trigger

A parent order becomes `completed` when every remaining sub-order is delivered and the holdback period has passed. The maintenance loop is what moves it.

## Shipping was missing from the data model

Each shop has a flat `shipping_fee_cents`. It is added to the sub-order, passed through to the vendor, and excluded from the commission base.
