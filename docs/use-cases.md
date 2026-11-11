# Use cases

Screen map with full routing: [screen-routing.md](screen-routing.md).

| Actor | Wants | Screen | Endpoint |
| --- | --- | --- | --- |
| Guest | Browse shops and products | `/`, `/shops`, `/products/[id]`, `/search` | `GET /api/store/*` |
| Guest | Keep a cart before signing in | `/cart` | merged later with `POST /api/cart/merge` |
| Customer | Register with email OTP | `/register` (details → code) | `POST /api/auth/register`, `POST /api/auth/verify-email`, `POST /api/auth/resend-otp` |
| Customer | Sign in | `/login` | `POST /api/auth/login` (403 `email_unverified` until OTP done) |
| Customer | Pay (sign in or register OTP on the page) | `/checkout` | `POST /api/checkout`, `POST /api/payments/{id}/confirm` |
| Customer | Receive an e-receipt after pay | mailbox / email | sent from checkout confirm |
| Customer | Track each shop's parcel | `/account/orders/[id]` | `GET /api/account/orders/{id}` |
| Customer | Review a delivered item | product page, `/account` | `POST /api/account/reviews` |
| Customer | Open a dispute | order detail | `POST /api/account/sub-orders/{id}/dispute` |
| Customer | Apply to sell (OTP if needed, shop photo required) | `/sell` | `POST /api/vendor-applications` (+ `shop_image`) |
| Vendor | Publish catalogue with photo, price, description | `/seller/products` | `POST /api/seller/products`, `…/submit`, `…/image` |
| Vendor | Run a shop discount | `/seller/promotions` | `POST /api/seller/coupons` |
| Vendor | Update storefront photo | `/seller/storefront` | `POST /api/seller/shop/image` |
| Vendor | Fulfil only their sub-order | `/seller/orders` | `POST /api/seller/orders/{id}/ship` |
| Vendor | See earnings and request a payout | `/seller/payouts` | `GET /api/seller/earnings`, `POST /api/seller/payouts` |
| Vendor | Reply to a review without changing the stars | `/seller/reviews` | `POST /api/seller/reviews/{id}/reply` |
| Admin | Verify a shop | `/admin/vendors` | `POST /api/vendors/{id}/documents/{doc}/review`, `POST /api/vendors/{id}/verify` |
| Admin | Publish or reject a listing | `/admin/listings` | `POST /api/listings/{id}/approve`, `…/reject` |
| Admin | Revise a commission rate | `/admin/commissions` | `POST /api/commission-rules/{id}/revise` |
| Admin | Export a report | `/admin/reports` | `GET /api/reports/sales/export` |
| Support | Read the activity log and moderate a review | `/admin/audit`, `/admin/reviews` | `GET /api/audit-logs`, `POST /api/reviews/{id}/flag` |
| Support | Co-sign a payout | `/admin/payouts` | `POST /api/payouts/{id}/approve` |
| Super Admin | Change the permission matrix | `/admin/roles` | `DELETE /api/roles/{id}/permissions/{key}` |
| Super Admin | Archive the log | Swagger or the audit API | `POST /api/audit-logs/archive` |
| System | Release an expired checkout and complete a delivered order | maintenance loop | `app.services.maintenance.tick` |
