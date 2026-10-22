# Sequences

## Split checkout

```mermaid
sequenceDiagram
  participant Maya
  participant Web
  participant API
  participant DB
  Maya->>Web: Pay
  Web->>API: POST /api/checkout
  API->>DB: Reserve stock if on_hand - reserved >= qty
  API-->>Maya: Payment intent
  Maya->>API: POST /api/payments/{id}/confirm
  API->>DB: One parent order, one sub-order per shop
  API->>DB: Frozen commission lines and a balanced journal
  API->>DB: Delete the purchased cart lines as the customer
  API-->>Maya: Order id
```

Confirming the same intent again returns the same order. A declined test card releases the reservation and the coupon use.

## Two-person payout

```mermaid
sequenceDiagram
  participant Jess
  participant Daniel
  participant Lin
  participant Ledger
  Jess->>Jess: POST /api/seller/payouts/PAY-06/request
  Daniel->>Daniel: First signature, status pending_second_approval
  Daniel-->>Daniel: Second signature is 409 already_signed
  Jess-->>Jess: Approve is 403
  Lin->>Lin: Second signature, status approved
  Daniel->>Ledger: Pay with a bank reference
  Ledger-->>Daniel: vendor_payable debit, cash credit
```

An open dispute refuses a new request with `dispute_open` and leaves the held payout where it is.
