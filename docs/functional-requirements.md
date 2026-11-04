# Functional Requirements — Bazaar

Bazaar is a multi-vendor marketplace: many independent shops, one checkout, and clear control over money, access, and accountability.

## 1. Customer shopping

Customers can browse shops and products, search the catalogue, and read published reviews; keep a guest cart before signing in and merge it into the account cart after login; apply coupons, save items to a wishlist, and check out in one payment; track each shop’s parcel separately after the order is placed; and confirm delivery, leave reviews, or open a dispute when something goes wrong.

## 2. Seller operations

Sellers can manage products, variants, and inventory for their own shop only; fulfil and ship only their part of a multi-shop order; run promotions or shop coupons and reply to customer reviews without changing the star rating; view earnings and request payouts; and cannot see another seller’s products, orders, or payouts because of tenant isolation.

## 3. Admin and support operations

Admins and support staff can approve new seller applications and review vendor documents; manage categories, platform coupons, and customer or review moderation; resolve disputes and oversee open orders across the platform; set and revise commission rules; and approve payouts and export operational reports scoped by role.

## 4. Checkout, commission, and payouts

One customer payment can include items from many shops; the order then splits into one sub-order per shop so each shop ships its own parcel; commission is locked at payment time so later rate changes do not rewrite past orders; money is tracked in cents and coupon discounts are split fairly across shops; and payouts need two different staff members to approve before money is marked paid.

## 5. Safety, roles, and activity log

Roles and permissions limit what each user can open (customer, seller, admin, support, super admin); sellers and customers only reach their own data and cross-tenant access returns not found; every important create, update, delete, sign-in, and denied attempt is written to an activity log; sensitive tables (audit, commission, ledger) are protected so the app role cannot quietly rewrite history; and sessions use a secure browser cookie while staff tools stay behind authentication.

## Out of scope for this product

Page builders, visual drag-and-drop site editors, and MongoDB-stored page designs are not part of Bazaar. This marketplace stores business data in PostgreSQL and serves a fixed Next.js storefront, Seller Central, and Admin Console.
