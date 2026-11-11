# Bazaar Platform

A multi-vendor marketplace with three surfaces: public **Website**, **Seller Dashboard**, and **Admin Console**. Customers buy from many shops in one checkout. Each shop ships its own part of the order. The platform freezes commission at payment and uses maker-checker for shop go-live, product listings, and payouts.

**Stack:** Next.js (browser origin) → Flask API → PostgreSQL with row-level security. Sessions use a JWT cookie. Money is integer cents. Audit log is append-only for the app DB role.

- `backend/` Flask and PostgreSQL. Swagger UI is at `/api/docs`.
- `frontend/` Next.js storefront, Seller Dashboard, and Admin Console. The browser only talks to Next.js; `/api` and `/media` are forwarded to the API.
- `docs/` system requirements, roles, architecture, and diagrams. Start with [docs/system-requirements.md](docs/system-requirements.md).

## Run it on this Mac

Postgres is already expected on `127.0.0.1:5432` with roles `bazaar_owner` and `bazaar_app` and databases `bazaar` and `bazaar_test`. If those are missing:

```bash
backend/scripts/create_db.sh
cd backend && uv run alembic upgrade head && uv run python -m app.seed
```

`alembic upgrade head` includes migration **0006** (`email_verified_at`, `email_challenges`) for OTP signup. With SMTP off, OTP codes and e-receipts land in `backend/private/mailbox/`. Screen map: [docs/screen-routing.md](docs/screen-routing.md).

Then, from this folder:

```bash
chmod +x dev.sh start.sh
./dev.sh
```

`dev.sh` binds the API to `0.0.0.0:8000` and the web app to `0.0.0.0:3000`, and prints the address other computers on the network should open. Do not bookmark an old LAN address; the script detects the current one.

`./start.sh` builds Next.js and serves that build. Use it when someone on another computer should open the site: Next.js dev mode refuses some of those requests.

| On this Mac | On another device |
| --- | --- |
| http://127.0.0.1:3000 | `http://<printed-lan-ip>:3000` |
| http://127.0.0.1:3000/api/docs | `http://<printed-lan-ip>:3000/api/docs` |

The API is also reachable directly at port 8000. Swagger's **Authorize** button uses the email as the username and `demo` as the password.

## Demo accounts

Every password is `demo`.

| Email | Role | Opens |
| --- | --- | --- |
| maya@bazaar.local | Customer | `/account` |
| jess@annescraftworks.local | Vendor, AnnesCraftworks | `/seller` |
| kein@keinmaker.local | Vendor, KeinMaker | `/seller` |
| ava@bazaar.local | Admin | `/admin` |
| daniel@bazaar.local | Super Admin | `/admin` |
| lin@bazaar.local | Support | `/admin` |
| theo@mail.local | Customer | `/account` |

The login page lists the same accounts and signs you in when you click a card.

Test card `4242 4242 4242 4242` is approved. `4000 0000 0000 0002` is declined and the reserved stock is released.

## Pages

Primary sidebar routes (full map + flows: [docs/screen-routing.md](docs/screen-routing.md)):

| Area | Sidebar URLs |
| --- | --- |
| Shop | `/`, `/shops`, `/shops/[slug]`, `/products/[id]`, `/search`, `/cart`, `/checkout`, `/register`, `/login`, `/sell`, `/reviews`, `/about`, `/guide` |
| Customer | `/account`, `/account/orders`, `/account/settings` (+ wishlist / messages / notifications as deep links) |
| Seller | `/seller`, `/seller/products`, `/seller/orders`, `/seller/promotions`, `/seller/storefront`, `/seller/payouts` |
| Admin | `/admin`, `/admin/vendors`, `/admin/listings`, `/admin/disputes`, `/admin/reports`, `/admin/roles` |

Deep-link staff/seller screens still work (inventory, audit, commissions, payouts, etc.).

## Tests and docs

```bash
cd backend
uv run pytest
uv run python scripts/gen_docs.py
```

Pytest uses the `bazaar_test` database and the `bazaar_app` role, so row-level security is real. `STRICT_AUDIT` is on: a successful mutation that writes no audit row fails the suite.

## Docker

Homebrew Postgres can stay on 5432. Compose publishes Postgres on **5433**:

```bash
docker compose up --build
```

The API container migrates and loads the demo seed on start, which replaces whatever was in that database. The site is http://127.0.0.1:3000 and Swagger is http://127.0.0.1:3000/api/docs.
