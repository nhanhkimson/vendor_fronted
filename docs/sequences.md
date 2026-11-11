# Sequences

Screen routes for these flows: [screen-routing.md](screen-routing.md).

## Register with email OTP

```mermaid
sequenceDiagram
  participant User
  participant Web
  participant API
  participant Mail
  User->>Web: /register details
  Web->>API: POST /api/auth/register
  API->>Mail: 6-digit code (mailbox or SMTP)
  API-->>Web: challenge_id (+ dev_code in demo)
  User->>Web: Enter code
  Web->>API: POST /api/auth/verify-email
  API-->>Web: Session cookie + MeOut
  Web-->>User: next path or home
```

Unverified accounts cannot `POST /api/auth/login` (`email_unverified`). Resend uses `POST /api/auth/resend-otp`.

## Split checkout (+ e-receipt)

```mermaid
sequenceDiagram
  participant Maya
  participant Web
  participant API
  participant DB
  participant Mail
  Maya->>Web: Pay on /checkout
  Web->>API: POST /api/checkout
  API->>DB: Reserve stock if on_hand - reserved >= qty
  API-->>Maya: Payment intent
  Maya->>API: POST /api/payments/{id}/confirm
  API->>DB: One parent order, one sub-order per shop
  API->>DB: Frozen commission lines and a balanced journal
  API->>DB: Delete the purchased cart lines as the customer
  API->>Mail: E-receipt (mailbox or SMTP)
  API-->>Maya: Order id → /account/orders/{id}
```

Confirming the same intent again returns the same order. A declined test card releases the reservation and the coupon use. Mail failure never rolls back a successful payment.

## Open a shop with photo

```mermaid
sequenceDiagram
  participant Seller
  participant Web
  participant API
  Seller->>Web: /sell OTP (if needed)
  Seller->>Web: Name + shop photo
  Web->>API: POST /api/vendor-applications (multipart shop_image)
  API-->>Web: MeOut kind=vendor
  Web-->>Seller: /seller/products
```

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
