# Test evidence

| Evidence | Test |
| --- | --- |
| Section 10 permission matrix | `test_section10_every_route_has_a_permission_and_mutating_routes_audit` |
| Section 10 isolation | `test_g2_and_section10_vendor_isolation_is_404_and_rls` |
| Section 10 split order | `test_g3_one_payment_two_suborders_and_two_tracking_numbers` |
| Section 10 temporal commission | `test_g4_changing_the_rate_does_not_rewrite_history` |
| Section 10 audit and SQL denial | `test_section10_audit_records_role_at_the_time_and_sql_cannot_change_the_log` |
| Section 10 separation of duties | `test_section10_payout_needs_two_people_and_an_open_dispute_blocks_it` |
| Gate G1 | `test_g1_support_cannot_change_rules_and_admin_action_is_audited` |
| Gate G2 | `test_g2_and_section10_vendor_isolation_is_404_and_rls` |
| Gate G3 | `test_g3_one_payment_two_suborders_and_two_tracking_numbers` |
| Gate G4 | `test_g4_changing_the_rate_does_not_rewrite_history` |
| Gate G5 | `test_g5_seeded_demo_ledger_and_sub_orders_balance` |
| Corrected Appendix B | `test_appendix_b_customer_pays_90_and_commission_base_stays_full` |
| Platform coupon keeps the commission base | `test_platform_coupon_does_not_shrink_the_frozen_commission_base` |
| Last Super Admin and support | `test_last_super_admin_and_support_cannot_promote_themselves` |
| Permission revoke is immediate | `test_revoke_permission_takes_effect_on_the_next_request` |
| Vendor CSV is only their shop | `test_low_stock_notification_and_vendor_csv_is_only_their_shop` |

Pytest exit code: 0

```
....................                                                     [100%]
20 passed in 5.41s
```
