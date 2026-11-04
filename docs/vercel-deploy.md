# Deploy Bazaar to Vercel

Live projects (Hobby):

| App | URL |
| --- | --- |
| Storefront | https://bazaar-web-rho.vercel.app |
| API + Swagger | https://bazaar-api-phi.vercel.app/api/docs |
| Health | https://bazaar-api-phi.vercel.app/api/health |

API runtime is **Flask** (Python) on Vercel. Postgres is **Neon** (`bazaar-db`), with `bazaar_owner` / `bazaar_app` roles. The web app proxies `/api` and `/media` to the API via `API_URL`.

## Redeploy

```bash
# API
cd backend && vercel --prod --yes

# Web
cd frontend && vercel --prod --yes
```

## Env (already set on the Vercel projects)

**bazaar-api:** `DATABASE_URL`, `OWNER_DATABASE_URL`, `JWT_SECRET`, `COOKIE_SECURE=true`, `RUN_MAINTENANCE=false`, `ENVIRONMENT=production`

**bazaar-web:** `API_URL=https://bazaar-api-phi.vercel.app`, `JWT_SECRET` (same as API)

## Notes

- SSO Deployment Protection is off for both projects so the demo is public.
- Background maintenance is off on serverless; unpaid reservations will not auto-expire until you add a cron that hits a maintenance route.
- Local secrets used during setup: `backend/.env.vercel.secrets`, `backend/.jwt.secret` (gitignored).
