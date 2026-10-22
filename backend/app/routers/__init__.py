from app.routers import (
    audit,
    auth,
    categories,
    messages,
    notifications,
    orders,
    products,
    roles,
    storefront,
    system,
    vendors,
)

ROUTERS = [
    auth.router,
    storefront.router,
    roles.router,
    audit.router,
    vendors.router,
    products.router,
    categories.router,
    orders.router,
    messages.router,
    notifications.router,
    system.router,
]
