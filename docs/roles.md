# Role capabilities — Bazaar

Source of truth: [`backend/app/core/permissions.py`](../backend/app/core/permissions.py) (`SYSTEM_ROLES` and grant lists). There are **five** system roles. Super Admin inherits Admin, then adds governance permissions.

Password for every demo account is `demo`.

## Role map

| Role | Id | Home | Demo accounts |
|------|----|------|---------------|
| Customer | `customer` | `/account` | Maya R. (`maya@bazaar.local`), Theo P. (`theo@mail.local`) |
| Vendor (Seller) | `vendor` | `/seller` | Jess A. (`jess@annescraftworks.local`), Kein Maker (`kein@keinmaker.local`) |
| Support Agent | `support` | `/admin` | Lin S. (`lin@bazaar.local`) |
| Admin | `admin` | `/admin` | Ava K. (`ava@bazaar.local`) |
| Super Admin | `super_admin` | `/admin` | Daniel O. (`daniel@bazaar.local`) |

## Shared money rule

Payouts need **two different staff** members with `payout:approve`. Vendors only have `payout:request`. Commission on an order is frozen at payment time.

---

## 1. Customer

Shops, pays, tracks own orders, reviews delivered items, and opens disputes.

### Can do

- Browse shops and products; keep a cart; apply coupons; check out and pay
- View and cancel own orders; confirm delivery
- Message sellers; leave reviews on delivered purchases
- Open disputes on own sub-orders

### Cannot do

- Open Seller Central or Admin Console
- Request or approve payouts; change commission; see other users’ data

### Permission keys

| Module | Keys |
|--------|------|
| Orders | `order:create`, `order:read`, `order:cancel`, `order:confirm_delivery`, `dispute:create` |
| Messages | `message:create`, `message:read` |
| Reviews | `review:create`, `review:read` |
| Coupons | `coupon:apply` |

Banned customers lose: `order:create`, `review:create`, `coupon:apply`, `dispute:create`, `message:create`.

---

## 2. Vendor (Seller)

Runs one shop. Every read and write is limited to that vendor’s own rows (tenant isolation).

### Can do (own shop only)

- Products, variants, inventory: create, edit, archive, stock adjust, CSV import
- Fulfil own sub-orders: status, tracking, cancel before ship
- Shop coupons; reply to own product reviews; messages with customers
- View own commission lines and reports; **request** payouts

### Cannot do

- See another shop’s orders, products, or payouts (looks like not found)
- Approve payouts; edit platform commission rules; verify vendors; manage roles

### Permission keys

| Module | Keys |
|--------|------|
| Vendors | `vendor:read`, `vendor:update` |
| Products & stock | `product:create`, `product:read`, `product:update`, `product:delete`, `product:import`, `stock:read`, `stock:adjust` |
| Categories | `category:read`, `tag:assign` |
| Orders | `order:read`, `order:update_status`, `order:add_tracking`, `order:cancel`, `dispute:read` |
| Messages | `message:create`, `message:read` |
| Commission & payouts | `commission:read`, `payout:read`, `payout:request` |
| Reviews | `review:read`, `review:respond` |
| Coupons | `coupon:create`, `coupon:read`, `coupon:update`, `coupon:delete` |
| Reports | `report:read`, `report:export` |

---

## 3. Support Agent

Reconstructs events, moderates reviews, resolves disputes, and signs payouts. Cannot edit commission rates.

### Can do

- Read and export the activity log
- Read vendors, products, stock, categories, orders, customers, coupons, reports
- Update order status; resolve disputes; moderate reviews; ban customers
- Read commission and payouts; **sign payouts** (one of the two required signatures)

### Cannot do

- Edit commission rates; create or edit coupons
- Verify or suspend vendors; assign commission tiers
- Create, edit, or delete roles; archive the audit log; reset demo data

### Permission keys

| Module | Keys |
|--------|------|
| Audit | `audit:read`, `audit:export` |
| Vendors / catalogue | `vendor:read`, `product:read`, `product:moderate`, `stock:read`, `category:read` |
| Orders | `order:read`, `order:update_status`, `dispute:read`, `dispute:resolve`, `message:read` |
| Commission & payouts | `commission:read`, `payout:read`, `payout:approve` |
| Customers & reviews | `customer:read`, `customer:ban`, `review:read`, `review:moderate` |
| Coupons / reports | `coupon:read`, `report:read` |

---

## 4. Admin

Day-to-day platform operations: vendors, catalogue rules, orders, coupons, commission, and payouts.

### Can do

- Everything Support can for day-to-day ops, plus:
- Verify or suspend vendors; assign commission tiers; soft-delete vendors; create vendor records
- Manage categories and tags; update products and stock in the platform view
- Manage coupons; manage commission rules; customer create / update / delete / ban
- Approve payouts; export reports; read and export the activity log (not archive)
- View the permission matrix (`role:read`)

### Cannot do

- Create, update, or delete roles; assign roles to users
- Archive the activity log; run `system:reset`

### Permission keys

| Module | Keys |
|--------|------|
| Roles | `role:read` |
| Audit | `audit:read`, `audit:export` |
| Vendors | `vendor:create`, `vendor:read`, `vendor:update`, `vendor:delete`, `vendor:verify`, `vendor:suspend`, `vendor:assign_tier` |
| Products & stock | `product:read`, `product:update`, `product:moderate`, `stock:read` |
| Categories | `category:create`, `category:read`, `category:update`, `category:delete`, `tag:create`, `tag:assign`, `tag:delete` |
| Orders | `order:read`, `order:update_status`, `order:cancel`, `dispute:read`, `dispute:resolve`, `message:read` |
| Commission & payouts | `commission:read`, `commission:manage_rule`, `payout:read`, `payout:approve` |
| Customers & reviews | `customer:create`, `customer:read`, `customer:update`, `customer:delete`, `customer:ban`, `review:read`, `review:moderate` |
| Coupons | `coupon:create`, `coupon:read`, `coupon:update`, `coupon:delete` |
| Reports | `report:read`, `report:export` |

---

## 5. Super Admin

Platform owner. Inherits **all Admin grants** via parent role `admin`, then adds governance.

### Can do

- Full Admin capabilities, plus:
- Create, update, and delete custom roles; assign roles to users
- Archive the activity log; reset demo data

### Cannot do

- Bypass permission checks or tenant isolation outside the APIs those permissions allow

### Extra permission keys (on top of Admin)

| Module | Keys |
|--------|------|
| Roles | `role:create`, `role:update`, `role:delete`, `user:assign_role` |
| Audit / system | `audit:archive`, `system:reset` |

Effective Super Admin set = `ADMIN_GRANTS` + `SUPER_ADMIN_GRANTS`.
