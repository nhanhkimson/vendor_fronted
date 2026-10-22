from app.routers import audit, auth, categories, notifications, products, roles, storefront, system, vendors

ROUTERS = [
    auth.router,
    storefront.router,
    roles.router,
    audit.router,
    vendors.router,
    products.router,
    categories.router,
    notifications.router,
    system.router,
]
