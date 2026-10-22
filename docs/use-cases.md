# Use cases

| Actor | Wants | Screen | Endpoint |
| --- | --- | --- | --- |
| Guest | Browse shops and products | `/`, `/shops`, `/products/[id]`, `/search` | `GET /api/store/*` |
| Guest | Keep a cart before signing in | `/cart` | merged later with `POST /api/cart/merge` |
| Customer | Sign in or register | `/login`, `/register` | `POST /api/auth/login`, `POST /api/auth/register` |
| Customer | Pay for items from more than one shop | `/checkout` | `POST /api/checkout`, `POST /api/payments/{id}/confirm` |
| Customer | Track each shop's parcel | `/account/orders/[id]` | `GET /api/account/orders/{id}` |
| Customer | Review a delivered item | product page, `/account` | `POST /api/account/reviews` |
| Customer | Open a dispute | order detail | `POST /api/account/sub-orders/{id}/dispute` |
| Customer | Apply to sell | `/sell` | `POST /api/vendor-applications` |
| Vendor | Fulfil only their sub-order | `/seller/orders` | `POST /api/seller/orders/{id}/ship` |
| Vendor | See earnings and request a payout | `/seller/payouts` | `GET /api/seller/earnings`, `POST /api/seller/payouts` |
| Vendor | Reply to a review without changing the stars | `/seller/reviews` | `POST /api/seller/reviews/{id}/reply` |
| Admin | Verify a shop | `/admin/vendors` | `POST /api/vendors/{id}/documents/{doc}/review`, `POST /api/vendors/{id}/verify` |
| Admin | Revise a commission rate | `/admin/commissions` | `POST /api/commission-rules/{id}/revise` |
| Admin | Export a report | `/admin/reports` | `GET /api/reports/sales/export` |
| Support | Read the activity log and moderate a review | `/admin/audit`, `/admin/reviews` | `GET /api/audit-logs`, `POST /api/reviews/{id}/flag` |
| Support | Co-sign a payout | `/admin/payouts` | `POST /api/payouts/{id}/approve` |
| Super Admin | Change the permission matrix | `/admin/roles` | `DELETE /api/roles/{id}/permissions/{key}` |
| Super Admin | Archive the log | Swagger or the audit API | `POST /api/audit-logs/archive` |
| System | Release an expired checkout and complete a delivered order | maintenance loop | `app.services.maintenance.tick` |
