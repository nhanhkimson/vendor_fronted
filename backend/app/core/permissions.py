"""Permission catalogue (research Appendix A, extended) and the seeded role grants."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Module:
    id: str
    code: str
    name: str
    tag: str


MODULES: list[Module] = [
    Module("roles", "M1", "Roles & Permissions", "M1 Roles & Permissions"),
    Module("audit", "M2", "Activity Log", "M2 Activity Log"),
    Module("vendor", "M3", "Vendors", "M3 Vendors"),
    Module("product", "M4", "Products & Inventory", "M4 Products & Inventory"),
    Module("category", "M5", "Categories & Tags", "M5 Categories & Tags"),
    Module("order", "M6", "Orders & Fulfilment", "M6 Orders & Fulfilment"),
    Module("commission", "M7", "Commission & Payouts", "M7 Commission & Payouts"),
    Module("customer", "M8", "Customers & Reviews", "M8 Customers & Reviews"),
    Module("coupon", "M9", "Coupons & Promotions", "M9 Coupons & Promotions"),
    Module("report", "M10", "Reports & Analytics", "M10 Reports & Analytics"),
]
MODULE_BY_ID = {m.id: m for m in MODULES}

# key, module, action label, description
CATALOGUE: list[tuple[str, str, str, str]] = [
    ("role:create", "roles", "create", "Create custom roles"),
    ("role:read", "roles", "read", "View roles, users and the permission matrix"),
    ("role:update", "roles", "update", "Rename roles, set a parent, grant or revoke permissions"),
    ("role:delete", "roles", "delete", "Delete custom roles that no user holds"),
    ("user:assign_role", "roles", "assign", "Assign roles to users"),
    ("system:reset", "roles", "reset", "Reset the demo data to the seed"),
    ("audit:read", "audit", "read", "Search and filter the activity log"),
    ("audit:export", "audit", "export", "Export the activity log as CSV or JSON"),
    ("audit:archive", "audit", "archive", "Move the hot activity log into the archive"),
    ("vendor:create", "vendor", "create", "Create vendor records"),
    ("vendor:read", "vendor", "read", "View vendor details and verification documents"),
    ("vendor:update", "vendor", "update", "Edit vendor profiles (vendors: their own storefront)"),
    ("vendor:delete", "vendor", "delete", "Soft-delete a vendor with no open orders or unpaid earnings"),
    ("vendor:verify", "vendor", "verify", "Start review, verify or reject vendor applications"),
    ("vendor:suspend", "vendor", "suspend", "Suspend or reinstate a vendor"),
    ("vendor:assign_tier", "vendor", "tier", "Move a vendor to another commission tier"),
    ("product:create", "product", "create", "Create listings"),
    ("product:read", "product", "read", "View listings in Seller Central or the Admin Console"),
    ("product:update", "product", "update", "Edit listings, variants, images and activation"),
    ("product:delete", "product", "delete", "Archive listings"),
    ("product:import", "product", "bulk", "Bulk import listings from CSV"),
    ("stock:read", "product", "stock", "View stock per variant and warehouse"),
    ("stock:adjust", "product", "adjust", "Change on-hand stock"),
    ("category:create", "category", "create", "Create categories"),
    ("category:read", "category", "read", "View the category tree in the back office"),
    ("category:update", "category", "update", "Rename or move categories"),
    ("category:delete", "category", "delete", "Delete empty categories"),
    ("tag:create", "category", "tag", "Create tags"),
    ("tag:assign", "category", "assign", "Attach tags to listings"),
    ("tag:delete", "category", "untag", "Delete tags"),
    ("order:create", "order", "create", "Check out and pay"),
    ("order:read", "order", "read", "View orders (own orders, own shop, or all for staff)"),
    ("order:update_status", "order", "status", "Move sub-orders through fulfilment"),
    ("order:add_tracking", "order", "tracking", "Add a tracking number when shipping"),
    ("order:cancel", "order", "cancel", "Cancel before shipment (refunds automatically)"),
    ("order:confirm_delivery", "order", "confirm", "Confirm that a shipment arrived"),
    ("dispute:create", "order", "dispute", "Open a dispute on a sub-order"),
    ("dispute:read", "order", "disputes", "View disputes"),
    ("dispute:resolve", "order", "resolve", "Resolve disputes with or without a refund"),
    ("message:create", "order", "message", "Send messages between customers and vendors"),
    ("message:read", "order", "messages", "Read message threads"),
    ("commission:read", "commission", "read", "View commission rules, frozen lines and statements"),
    ("commission:manage_rule", "commission", "manage", "Create, edit (new version) and end commission rules"),
    ("payout:read", "commission", "payouts", "View payouts"),
    ("payout:request", "commission", "request", "Request a payout of the available balance"),
    ("payout:approve", "commission", "approve", "Sign a payout (two different people must sign)"),
    ("customer:create", "customer", "create", "Create customer accounts"),
    ("customer:read", "customer", "read", "View customers"),
    ("customer:update", "customer", "update", "Edit customer details"),
    ("customer:delete", "customer", "delete", "Deactivate customer accounts"),
    ("customer:ban", "customer", "ban", "Ban or unban customers"),
    ("review:create", "customer", "review", "Review a delivered purchase"),
    ("review:read", "customer", "reviews", "View reviews in the back office"),
    ("review:moderate", "customer", "moderate", "Flag, remove or restore reviews"),
    ("review:respond", "customer", "respond", "Reply to reviews of your own products"),
    ("coupon:create", "coupon", "create", "Create coupons"),
    ("coupon:read", "coupon", "read", "View coupons"),
    ("coupon:update", "coupon", "update", "Edit or pause coupons"),
    ("coupon:delete", "coupon", "delete", "Delete unused coupons"),
    ("coupon:apply", "coupon", "apply", "Apply a coupon at checkout"),
    ("report:read", "report", "read", "View dashboards and reports"),
    ("report:export", "report", "export", "Export reports as CSV"),
]
PERMISSION_KEYS = [row[0] for row in CATALOGUE]

# Keys removed from a banned customer's effective permissions.
BANNED_STRIPPED = frozenset(
    {"order:create", "review:create", "coupon:apply", "dispute:create", "message:create"}
)

ADMIN_GRANTS = [
    "role:read",
    "audit:read",
    "audit:export",
    "vendor:create",
    "vendor:read",
    "vendor:update",
    "vendor:delete",
    "vendor:verify",
    "vendor:suspend",
    "vendor:assign_tier",
    "product:read",
    "product:update",
    "stock:read",
    "category:create",
    "category:read",
    "category:update",
    "category:delete",
    "tag:create",
    "tag:assign",
    "tag:delete",
    "order:read",
    "order:update_status",
    "order:cancel",
    "dispute:read",
    "dispute:resolve",
    "message:read",
    "commission:read",
    "commission:manage_rule",
    "payout:read",
    "payout:approve",
    "customer:create",
    "customer:read",
    "customer:update",
    "customer:delete",
    "customer:ban",
    "review:read",
    "review:moderate",
    "coupon:create",
    "coupon:read",
    "coupon:update",
    "coupon:delete",
    "report:read",
    "report:export",
]

# Super Admin inherits Admin (parent) and adds platform governance.
SUPER_ADMIN_GRANTS = [
    "role:create",
    "role:update",
    "role:delete",
    "user:assign_role",
    "audit:archive",
    "system:reset",
]

SUPPORT_GRANTS = [
    "audit:read",
    "audit:export",
    "vendor:read",
    "product:read",
    "stock:read",
    "category:read",
    "order:read",
    "order:update_status",
    "dispute:read",
    "dispute:resolve",
    "message:read",
    "commission:read",
    "payout:read",
    "payout:approve",
    "customer:read",
    "customer:ban",
    "review:read",
    "review:moderate",
    "coupon:read",
    "report:read",
]

VENDOR_GRANTS = [
    "vendor:read",
    "vendor:update",
    "product:create",
    "product:read",
    "product:update",
    "product:delete",
    "product:import",
    "stock:read",
    "stock:adjust",
    "category:read",
    "tag:assign",
    "order:read",
    "order:update_status",
    "order:add_tracking",
    "order:cancel",
    "dispute:read",
    "message:create",
    "message:read",
    "commission:read",
    "payout:read",
    "payout:request",
    "review:read",
    "review:respond",
    "coupon:create",
    "coupon:read",
    "coupon:update",
    "coupon:delete",
    "report:read",
    "report:export",
]

CUSTOMER_GRANTS = [
    "order:create",
    "order:read",
    "order:cancel",
    "order:confirm_delivery",
    "dispute:create",
    "message:create",
    "message:read",
    "review:create",
    "review:read",
    "coupon:apply",
]

# id, name, kind, parent, locked, description, direct grants
SYSTEM_ROLES = [
    (
        "super_admin",
        "Super Admin",
        "platform",
        "admin",
        True,
        "Platform owner. Inherits Admin and adds roles, user assignment, audit archive and demo reset.",
        SUPER_ADMIN_GRANTS,
    ),
    (
        "admin",
        "Admin",
        "platform",
        None,
        False,
        "Day-to-day operations: vendors, catalogue rules, orders, coupons, commission and payouts.",
        ADMIN_GRANTS,
    ),
    (
        "support",
        "Support Agent",
        "platform",
        None,
        False,
        "Reconstructs events, moderates reviews, resolves disputes, signs payouts. Cannot edit rates.",
        SUPPORT_GRANTS,
    ),
    (
        "vendor",
        "Vendor",
        "vendor",
        None,
        False,
        "Runs one shop. Every read and write is limited to that vendor's own rows.",
        VENDOR_GRANTS,
    ),
    (
        "customer",
        "Customer",
        "customer",
        None,
        False,
        "Shops, pays, tracks own orders, reviews delivered items and opens disputes.",
        CUSTOMER_GRANTS,
    ),
]

for _role in SYSTEM_ROLES:
    for _key in _role[6]:
        assert _key in PERMISSION_KEYS, _key
