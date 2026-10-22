import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from app.core import handlers
from app.core.config import settings
from app.core.middleware import RequestContextMiddleware
from app.core.permissions import MODULES
from app.routers import ROUTERS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("bazaar")

DESCRIPTION = """
**Bazaar** is a multi-vendor marketplace. Customers buy from many independent shops in one
checkout, each shop fulfils its own part of the order, and the platform keeps a commission.
The Next.js storefront, Seller Central and Admin Console use exactly these endpoints.

### Try it here
1. Click **Authorize**. Username = a demo email below, password = `demo`.
2. Open a module, press **Try it out**, then **Execute**.

| Account | Role | Good for |
|---|---|---|
| `daniel@bazaar.local` | Super Admin | roles matrix, assign roles, archive the log, sign payouts |
| `ava@bazaar.local` | Admin | verify vendors, coupons, commission rules, disputes |
| `lin@bazaar.local` | Support Agent | activity log, review moderation, second payout signature |
| `jess@annescraftworks.local` | Vendor (AnnesCraftworks) | products, stock, orders, payouts |
| `kein@keinmaker.local` | Vendor (KeinMaker) | tenant isolation: cannot see Jess's shop |
| `maya@bazaar.local` | Customer | cart, checkout, orders, reviews, disputes |

### Conventions
- Money is in **cents** (`1250` = $12.50). Commission rates are **basis points** (`1500` = 15%).
- Each endpoint states the permission it needs. Missing permission returns `403`;
  another vendor's or customer's record returns `404`; an illegal state change returns `409`.
- Every create, update, delete, sign-in and denied attempt is written to the **M2 Activity Log**
  with actor, roles, IP, user agent, before/after and request id (`X-Request-ID`).
- Test cards: `4242 4242 4242 4242` is approved, `4000 0000 0000 0002` is declined.
"""

TAGS = [
    {"name": "Auth", "description": "Sign in, sign out, register, current user and effective permissions."},
    {"name": "Storefront", "description": "Public catalogue: products, shops, categories, reviews."},
    *[
        {"name": m.tag, "description": desc}
        for m, desc in zip(
            MODULES,
            [
                "Mandatory module. Roles, role hierarchy, the permission matrix and role assignment.",
                "Mandatory module. Append-only log of every mutation and denied attempt; export and archive.",
                "Vendor applications, documents, verification, suspension, tiers and storefronts.",
                "Listings, variants, images, stock per warehouse, CSV import and export.",
                "Category tree (with cycle protection) and tags.",
                "Cart, checkout, simulated payment, split sub-orders, fulfilment, cancellation, disputes.",
                "Versioned commission rules, frozen commission lines, ledger, statements, two-person payouts.",
                "Customers, bans, verified-purchase reviews, moderation and vendor replies.",
                "Platform-funded and vendor-funded coupons, flash windows and usage limits.",
                "GMV, commission, top products, acquisition and CSV exports.",
            ],
            strict=True,
        )
    ],
    {"name": "Notifications & Messages", "description": "In-app notifications and customer to vendor messages."},
    {"name": "System", "description": "Health check and demo reset."},
]


async def _maintenance_loop() -> None:
    from app.services.maintenance import tick

    while True:
        try:
            await run_in_threadpool(tick)
        except Exception:
            log.exception("maintenance tick failed")
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(_: FastAPI):
    task = asyncio.create_task(_maintenance_loop()) if settings.run_maintenance else None
    yield
    if task:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


app = FastAPI(
    title="Bazaar Marketplace API",
    version="1.0.0",
    description=DESCRIPTION,
    openapi_tags=TAGS,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    swagger_ui_parameters={
        "persistAuthorization": True,
        "docExpansion": "none",
        "filter": True,
        "displayRequestDuration": True,
        "tryItOutEnabled": True,
    },
    lifespan=lifespan,
)
app.add_middleware(RequestContextMiddleware)
handlers.install(app)

settings.media_dir.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=settings.media_dir), name="media")

for router in ROUTERS:
    app.include_router(router)
