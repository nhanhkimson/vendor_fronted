from app.routers import audit, auth, notifications, roles, system

ROUTERS = [
    auth.router,
    roles.router,
    audit.router,
    notifications.router,
    system.router,
]
