# Permission matrix

Direct grants. Super Admin's parent is Admin, so the effective set is both columns.

| Permission | Super Admin | Admin | Support Agent | Vendor | Customer |
| --- | --- | --- | --- | --- | --- |
| `role:create` | yes |  |  |  |  |
| `role:read` |  | yes |  |  |  |
| `role:update` | yes |  |  |  |  |
| `role:delete` | yes |  |  |  |  |
| `user:assign_role` | yes |  |  |  |  |
| `system:reset` | yes |  |  |  |  |
| `audit:read` |  | yes | yes |  |  |
| `audit:export` |  | yes | yes |  |  |
| `audit:archive` | yes |  |  |  |  |
| `vendor:create` |  | yes |  |  |  |
| `vendor:read` |  | yes | yes | yes |  |
| `vendor:update` |  | yes |  | yes |  |
| `vendor:delete` |  | yes |  |  |  |
| `vendor:verify` |  | yes |  |  |  |
| `vendor:suspend` |  | yes |  |  |  |
| `vendor:assign_tier` |  | yes |  |  |  |
| `product:create` |  |  |  | yes |  |
| `product:read` |  | yes | yes | yes |  |
| `product:update` |  | yes |  | yes |  |
| `product:delete` |  |  |  | yes |  |
| `product:import` |  |  |  | yes |  |
| `stock:read` |  | yes | yes | yes |  |
| `stock:adjust` |  |  |  | yes |  |
| `category:create` |  | yes |  |  |  |
| `category:read` |  | yes | yes | yes |  |
| `category:update` |  | yes |  |  |  |
| `category:delete` |  | yes |  |  |  |
| `tag:create` |  | yes |  |  |  |
| `tag:assign` |  | yes |  | yes |  |
| `tag:delete` |  | yes |  |  |  |
| `order:create` |  |  |  |  | yes |
| `order:read` |  | yes | yes | yes | yes |
| `order:update_status` |  | yes | yes | yes |  |
| `order:add_tracking` |  |  |  | yes |  |
| `order:cancel` |  | yes |  | yes | yes |
| `order:confirm_delivery` |  |  |  |  | yes |
| `dispute:create` |  |  |  |  | yes |
| `dispute:read` |  | yes | yes | yes |  |
| `dispute:resolve` |  | yes | yes |  |  |
| `message:create` |  |  |  | yes | yes |
| `message:read` |  | yes | yes | yes | yes |
| `commission:read` |  | yes | yes | yes |  |
| `commission:manage_rule` |  | yes |  |  |  |
| `payout:read` |  | yes | yes | yes |  |
| `payout:request` |  |  |  | yes |  |
| `payout:approve` |  | yes | yes |  |  |
| `customer:create` |  | yes |  |  |  |
| `customer:read` |  | yes | yes |  |  |
| `customer:update` |  | yes |  |  |  |
| `customer:delete` |  | yes |  |  |  |
| `customer:ban` |  | yes | yes |  |  |
| `review:create` |  |  |  |  | yes |
| `review:read` |  | yes | yes | yes | yes |
| `review:moderate` |  | yes | yes |  |  |
| `review:respond` |  |  |  | yes |  |
| `coupon:create` |  | yes |  | yes |  |
| `coupon:read` |  | yes | yes | yes |  |
| `coupon:update` |  | yes |  | yes |  |
| `coupon:delete` |  | yes |  | yes |  |
| `coupon:apply` |  |  |  |  | yes |
| `report:read` |  | yes | yes | yes |  |
| `report:export` |  | yes |  | yes |  |
