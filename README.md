# Bazaar Platform

A multi-vendor marketplace. Customers buy from many shops in one checkout. Each shop ships its own part of the order. The platform keeps a commission that is frozen when the order is placed.

- `backend/` FastAPI and PostgreSQL. Swagger UI is at `/api/docs`.
- `frontend/` Next.js storefront, Seller Central, and Admin Console. The browser only talks to Next.js; `/api` and `/media` are forwarded to FastAPI.
- `docs/` architecture, use cases, and diagrams generated from the code.

## Run it on this Mac

Postgres is already expected on `127.0.0.1:5432` with roles `bazaar_owner` and `bazaar_app` and databases `bazaar` and `bazaar_test`. If those are missing:

```bash
backend/scripts/create_db.sh
cd backend && uv run alembic upgrade head && uv run python -m app.seed
```

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

| Area | URL |
| --- | --- |
| Shop | `/`, `/shops`, `/shops/[slug]`, `/products/[id]`, `/search`, `/cart`, `/checkout`, `/reviews`, `/sell`, `/about`, `/guide` |
| Customer | `/account`, `/account/orders`, `/account/wishlist`, `/account/messages`, `/account/notifications`, `/account/settings` |
| Seller | `/seller`, `/seller/products`, `/seller/inventory`, `/seller/orders`, `/seller/promotions`, `/seller/payouts`, `/seller/reports`, `/seller/storefront`, `/seller/messages`, `/seller/reviews` |
| Admin | `/admin`, `/admin/vendors`, `/admin/products`, `/admin/categories`, `/admin/orders`, `/admin/customers`, `/admin/reviews`, `/admin/coupons`, `/admin/disputes`, `/admin/roles`, `/admin/audit`, `/admin/commissions`, `/admin/payouts`, `/admin/reports` |

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
