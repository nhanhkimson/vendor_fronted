# API map

Every route declares a permission. Every mutating route declares the audit action written with the change.

| Method | Path | Permission | Scope | Audit |
| --- | --- | --- | --- | --- |
| GET | `/api/account/messages` | `message:read` | customer |  |
| POST | `/api/account/messages` | `message:create` | customer | order.start_conversation |
| GET | `/api/account/messages/{conversation_id}` | `message:read` | customer |  |
| POST | `/api/account/messages/{conversation_id}/reply` | `message:create` | customer | order.reply_message |
| GET | `/api/account/orders` | `order:read` | customer |  |
| GET | `/api/account/orders/{order_id}` | `order:read` | customer |  |
| GET | `/api/account/reviews` | `review:read` | customer |  |
| POST | `/api/account/reviews` | `review:create` | customer | customer.create_review |
| POST | `/api/account/sub-orders/{sub_id}/cancel` | `order:cancel` | customer | order.cancel |
| POST | `/api/account/sub-orders/{sub_id}/confirm-delivery` | `order:confirm_delivery` | customer | order.confirm_delivery |
| POST | `/api/account/sub-orders/{sub_id}/dispute` | `dispute:create` | customer | order.open_dispute |
| GET | `/api/account/summary` | `order:read` | customer |  |
| GET | `/api/account/wishlist` | `authenticated` | customer |  |
| POST | `/api/account/wishlist` | `authenticated` | customer | customer.wishlist_add |
| DELETE | `/api/account/wishlist/{product_id}` | `authenticated` | customer | customer.wishlist_remove |
| GET | `/api/admin/summary` | `report:read` | platform |  |
| GET | `/api/audit-logs` | `audit:read` | platform |  |
| GET | `/api/audit-logs/archive` | `audit:read` | platform |  |
| POST | `/api/audit-logs/archive` | `audit:archive` | platform | audit.archive |
| GET | `/api/audit-logs/export` | `audit:export` | platform |  |
| GET | `/api/audit-logs/facets` | `audit:read` | platform |  |
| GET | `/api/auth/demo-accounts` | `public` | public |  |
| POST | `/api/auth/login` | `public` | public | identity.login |
| POST | `/api/auth/logout` | `authenticated` | customer | identity.logout |
| GET | `/api/auth/me` | `authenticated` | customer |  |
| POST | `/api/auth/register` | `public` | public | identity.register |
| POST | `/api/auth/token` | `public` | public | identity.login |
| GET | `/api/cart` | `order:create` | customer |  |
| DELETE | `/api/cart/coupon` | `coupon:apply` | customer | coupon.remove |
| POST | `/api/cart/coupon` | `coupon:apply` | customer | coupon.apply |
| POST | `/api/cart/items` | `order:create` | customer | order.cart_add |
| DELETE | `/api/cart/items/{line_id}` | `order:create` | customer | order.cart_remove |
| PATCH | `/api/cart/items/{line_id}` | `order:create` | customer | order.cart_update |
| POST | `/api/cart/merge` | `order:create` | customer | order.cart_merge |
| GET | `/api/categories` | `category:read` | platform |  |
| POST | `/api/categories` | `category:create` | platform | category.create |
| DELETE | `/api/categories/{category_id}` | `category:delete` | platform | category.delete |
| PATCH | `/api/categories/{category_id}` | `category:update` | platform | category.update |
| POST | `/api/checkout` | `order:create` | customer | order.checkout |
| GET | `/api/commission-lines` | `commission:read` | platform |  |
| GET | `/api/commission-rules` | `commission:read` | platform |  |
| POST | `/api/commission-rules` | `commission:manage_rule` | platform | commission.create_rule |
| POST | `/api/commission-rules/{rule_id}/end` | `commission:manage_rule` | platform | commission.end_rule |
| POST | `/api/commission-rules/{rule_id}/revise` | `commission:manage_rule` | platform | commission.revise_rule |
| GET | `/api/coupons` | `coupon:read` | platform |  |
| POST | `/api/coupons` | `coupon:create` | platform | coupon.create |
| DELETE | `/api/coupons/{code}` | `coupon:delete` | platform | coupon.delete |
| PATCH | `/api/coupons/{code}` | `coupon:update` | platform | coupon.update |
| GET | `/api/customers` | `customer:read` | platform |  |
| POST | `/api/customers` | `customer:create` | platform | customer.create |
| GET | `/api/customers/{user_id}` | `customer:read` | platform |  |
| PATCH | `/api/customers/{user_id}` | `customer:update` | platform | customer.update |
| POST | `/api/customers/{user_id}/ban` | `customer:ban` | platform | customer.ban |
| POST | `/api/customers/{user_id}/deactivate` | `customer:delete` | platform | customer.deactivate |
| POST | `/api/customers/{user_id}/unban` | `customer:ban` | platform | customer.unban |
| GET | `/api/disputes` | `dispute:read` | platform |  |
| GET | `/api/disputes/{dispute_id}` | `dispute:read` | platform |  |
| POST | `/api/disputes/{dispute_id}/resolve` | `dispute:resolve` | platform | order.resolve_dispute |
| GET | `/api/health` | `public` | public |  |
| GET | `/api/inventory` | `stock:read` | platform |  |
| GET | `/api/ledger` | `commission:read` | platform |  |
| GET | `/api/ledger/trial-balance` | `commission:read` | platform |  |
| GET | `/api/messages` | `message:read` | platform |  |
| GET | `/api/messages/{conversation_id}` | `message:read` | platform |  |
| GET | `/api/notifications` | `authenticated` | customer |  |
| POST | `/api/notifications/read-all` | `authenticated` | customer | notification.read_all |
| POST | `/api/notifications/{notification_id}/read` | `authenticated` | customer | notification.read |
| GET | `/api/orders` | `order:read` | platform |  |
| POST | `/api/orders/sub-orders/{sub_id}/cancel` | `order:cancel` | platform | order.cancel |
| POST | `/api/orders/sub-orders/{sub_id}/status` | `order:update_status` | platform | order.update_status |
| GET | `/api/orders/{order_id}` | `order:read` | platform |  |
| GET | `/api/payments/{intent_id}` | `order:create` | customer |  |
| POST | `/api/payments/{intent_id}/confirm` | `order:create` | customer | order.create |
| GET | `/api/payouts` | `payout:read` | platform |  |
| GET | `/api/payouts/{payout_id}` | `payout:read` | platform |  |
| POST | `/api/payouts/{payout_id}/approve` | `payout:approve` | platform | commission.approve_payout |
| POST | `/api/payouts/{payout_id}/pay` | `payout:approve` | platform | commission.pay_payout |
| GET | `/api/permissions` | `role:read` | platform |  |
| GET | `/api/products` | `product:read` | platform |  |
| POST | `/api/products/{product_id}/moderate` | `product:update` | platform | product.moderate |
| PUT | `/api/products/{product_id}/tags` | `tag:assign` | platform | category.assign_tags |
| GET | `/api/reports/overview` | `report:read` | platform |  |
| GET | `/api/reports/{report}/export` | `report:export` | platform | report.export |
| GET | `/api/reviews` | `review:read` | platform |  |
| POST | `/api/reviews/{review_id}/flag` | `review:moderate` | platform | customer.flag |
| POST | `/api/reviews/{review_id}/remove` | `review:moderate` | platform | customer.remove |
| POST | `/api/reviews/{review_id}/restore` | `review:moderate` | platform | customer.restore |
| GET | `/api/roles` | `role:read` | platform |  |
| POST | `/api/roles` | `role:create` | platform | roles.create |
| DELETE | `/api/roles/{role_id}` | `role:delete` | platform | roles.delete |
| GET | `/api/roles/{role_id}` | `role:read` | platform |  |
| PATCH | `/api/roles/{role_id}` | `role:update` | platform | roles.update |
| PUT | `/api/roles/{role_id}/permissions` | `role:update` | platform | roles.update_permissions |
| DELETE | `/api/roles/{role_id}/permissions/{key}` | `role:update` | platform | roles.revoke |
| POST | `/api/roles/{role_id}/permissions/{key}` | `role:update` | platform | roles.grant |
| GET | `/api/seller/commission-lines` | `commission:read` | vendor |  |
| GET | `/api/seller/commission-rules` | `commission:read` | vendor |  |
| GET | `/api/seller/coupons` | `coupon:read` | vendor |  |
| POST | `/api/seller/coupons` | `coupon:create` | vendor | coupon.create |
| DELETE | `/api/seller/coupons/{code}` | `coupon:delete` | vendor | coupon.delete |
| PATCH | `/api/seller/coupons/{code}` | `coupon:update` | vendor | coupon.update |
| GET | `/api/seller/disputes` | `dispute:read` | vendor |  |
| POST | `/api/seller/documents/{doc_id}` | `vendor:update` | vendor | vendor.upload_document |
| GET | `/api/seller/documents/{doc_id}/file` | `vendor:read` | vendor |  |
| GET | `/api/seller/earnings` | `commission:read` | vendor |  |
| GET | `/api/seller/inventory` | `stock:read` | vendor |  |
| POST | `/api/seller/inventory/{variant_id}/adjust` | `stock:adjust` | vendor | product.adjust_stock |
| GET | `/api/seller/ledger` | `commission:read` | vendor |  |
| GET | `/api/seller/messages` | `message:read` | vendor |  |
| GET | `/api/seller/messages/{conversation_id}` | `message:read` | vendor |  |
| POST | `/api/seller/messages/{conversation_id}/reply` | `message:create` | vendor | order.reply_message |
| GET | `/api/seller/orders` | `order:read` | vendor |  |
| GET | `/api/seller/orders/{sub_id}` | `order:read` | vendor |  |
| POST | `/api/seller/orders/{sub_id}/accept` | `order:update_status` | vendor | order.accept |
| POST | `/api/seller/orders/{sub_id}/cancel` | `order:cancel` | vendor | order.cancel |
| POST | `/api/seller/orders/{sub_id}/deliver` | `order:update_status` | vendor | order.deliver |
| POST | `/api/seller/orders/{sub_id}/pack` | `order:update_status` | vendor | order.pack |
| POST | `/api/seller/orders/{sub_id}/ship` | `order:add_tracking` | vendor | order.ship |
| GET | `/api/seller/payouts` | `payout:read` | vendor |  |
| POST | `/api/seller/payouts` | `payout:request` | vendor | commission.request_payout |
| GET | `/api/seller/payouts/{payout_id}` | `payout:read` | vendor |  |
| POST | `/api/seller/payouts/{payout_id}/request` | `payout:request` | vendor | commission.request_payout |
| GET | `/api/seller/products` | `product:read` | vendor |  |
| POST | `/api/seller/products` | `product:create` | vendor | product.create |
| GET | `/api/seller/products/export` | `product:read` | vendor |  |
| POST | `/api/seller/products/import` | `product:import` | vendor | product.import |
| DELETE | `/api/seller/products/{product_id}` | `product:delete` | vendor | product.delete |
| GET | `/api/seller/products/{product_id}` | `product:read` | vendor |  |
| PATCH | `/api/seller/products/{product_id}` | `product:update` | vendor | product.update |
| POST | `/api/seller/products/{product_id}/image` | `product:update` | vendor | product.upload_image |
| POST | `/api/seller/products/{product_id}/restore` | `product:update` | vendor | product.restore |
| PUT | `/api/seller/products/{product_id}/tags` | `tag:assign` | vendor | category.assign_tags |
| POST | `/api/seller/products/{product_id}/variants` | `product:update` | vendor | product.add_variant |
| GET | `/api/seller/reports/overview` | `report:read` | vendor |  |
| GET | `/api/seller/reports/{report}/export` | `report:export` | vendor | report.export |
| GET | `/api/seller/reviews` | `review:read` | vendor |  |
| POST | `/api/seller/reviews/{review_id}/reply` | `review:respond` | vendor | customer.respond |
| GET | `/api/seller/shop` | `vendor:read` | vendor |  |
| PATCH | `/api/seller/shop` | `vendor:update` | vendor | vendor.update_shop |
| POST | `/api/seller/shop/image` | `vendor:update` | vendor | vendor.upload_image |
| POST | `/api/seller/shop/submit` | `vendor:update` | vendor | vendor.submit_application |
| GET | `/api/seller/summary` | `report:read` | vendor |  |
| PATCH | `/api/seller/variants/{variant_id}` | `product:update` | vendor | product.update_variant |
| GET | `/api/store/categories` | `public` | public |  |
| GET | `/api/store/home` | `public` | public |  |
| GET | `/api/store/products` | `public` | public |  |
| GET | `/api/store/products/{product_id}` | `public` | public |  |
| GET | `/api/store/promotions` | `public` | public |  |
| GET | `/api/store/reviews` | `public` | public |  |
| GET | `/api/store/shops` | `public` | public |  |
| GET | `/api/store/shops/{slug}` | `public` | public |  |
| GET | `/api/store/tags` | `public` | public |  |
| POST | `/api/system/reset` | `system:reset` | platform | system.reset |
| GET | `/api/tags` | `category:read` | platform |  |
| POST | `/api/tags` | `tag:create` | platform | category.create_tag |
| DELETE | `/api/tags/{tag_id}` | `tag:delete` | platform | category.delete_tag |
| GET | `/api/users` | `role:read` | platform |  |
| PUT | `/api/users/{user_id}/roles` | `user:assign_role` | platform | roles.assign |
| POST | `/api/vendor-applications` | `authenticated` | customer | vendor.submit_application |
| GET | `/api/vendors` | `vendor:read` | platform |  |
| POST | `/api/vendors` | `vendor:create` | platform | vendor.create |
| GET | `/api/vendors/tiers` | `vendor:read` | platform |  |
| DELETE | `/api/vendors/{vendor_id}` | `vendor:delete` | platform | vendor.delete |
| GET | `/api/vendors/{vendor_id}` | `vendor:read` | platform |  |
| PATCH | `/api/vendors/{vendor_id}` | `vendor:update` | platform | vendor.update |
| GET | `/api/vendors/{vendor_id}/documents/{doc_id}/file` | `vendor:verify` | platform |  |
| POST | `/api/vendors/{vendor_id}/documents/{doc_id}/review` | `vendor:verify` | platform | vendor.review_document |
| GET | `/api/vendors/{vendor_id}/earnings` | `commission:read` | platform |  |
| POST | `/api/vendors/{vendor_id}/reinstate` | `vendor:suspend` | platform | vendor.reinstate |
| POST | `/api/vendors/{vendor_id}/reject` | `vendor:verify` | platform | vendor.reject |
| POST | `/api/vendors/{vendor_id}/suspend` | `vendor:suspend` | platform | vendor.suspend |
| PUT | `/api/vendors/{vendor_id}/tier` | `vendor:assign_tier` | platform | vendor.assign_tier |
| POST | `/api/vendors/{vendor_id}/verify` | `vendor:verify` | platform | vendor.verify |
