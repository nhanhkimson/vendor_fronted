# State machines

Generated from `app/domain/states.py`. A transition that is not listed returns 409.

```mermaid
stateDiagram-v2
  draft --> under_review: submit application
  under_review --> active: verify
  under_review --> rejected: reject (reason)
  rejected --> under_review: resubmit documents
  active --> suspended: suspend (reason)
  suspended --> active: reinstate (reason)
```

Terminal: none.

```mermaid
stateDiagram-v2
  paid --> partially_fulfilled: some shops shipped
  paid --> fulfilled: every shop shipped
  paid --> partially_refunded: a shop cancelled
  paid --> cancelled: every shop cancelled
  partially_fulfilled --> fulfilled: every shop shipped
  partially_fulfilled --> partially_refunded: a shop cancelled or refunded
  fulfilled --> completed: all delivered and holdback passed
  fulfilled --> partially_refunded: a shop refunded
  fulfilled --> refunded: every shop refunded
  partially_refunded --> completed: the rest delivered and holdback passed
  partially_refunded --> refunded: the rest refunded
  partially_refunded --> cancelled: the rest cancelled
  completed
  cancelled
  refunded
```

Terminal: cancelled, completed, refunded.

```mermaid
stateDiagram-v2
  pending_acceptance --> accepted: vendor accepts
  pending_acceptance --> cancelled: cancel before shipping
  accepted --> packing: vendor packs
  accepted --> cancelled: cancel before shipping
  packing --> shipped: ship with tracking number
  packing --> cancelled: cancel before shipping
  shipped --> delivered: delivered
  shipped --> refunded: dispute resolved with refund
  delivered --> refunded: dispute resolved with refund
  cancelled
  refunded
```

Terminal: cancelled, refunded.

```mermaid
stateDiagram-v2
  eligible --> requested: vendor requests
  eligible --> held_for_dispute: dispute opened
  requested --> pending_second_approval: first approver signs
  requested --> held_for_dispute: dispute opened
  pending_second_approval --> approved: second, different approver signs
  pending_second_approval --> held_for_dispute: dispute opened
  approved --> paid: bank transfer sent
  approved --> held_for_dispute: dispute opened
  held_for_dispute --> eligible: dispute closed
  held_for_dispute --> requested: dispute closed
  held_for_dispute --> pending_second_approval: dispute closed
  held_for_dispute --> approved: dispute closed
  paid
```

Terminal: paid.

```mermaid
stateDiagram-v2
  published --> flagged: flag for moderation
  published --> removed: remove (reason)
  flagged --> published: restore
  flagged --> removed: remove (reason)
  removed --> published: restore
```

Terminal: none.

```mermaid
stateDiagram-v2
  open --> resolved_refund: refund the buyer
  open --> resolved_rejected: reject with reason
  resolved_refund
  resolved_rejected
```

Terminal: resolved_refund, resolved_rejected.
