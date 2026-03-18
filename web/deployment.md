# Web Deployment

## Production env

Keep real production values in an untracked `.env.deploy` at the repo root.

Start from the template:

```bash
cp .env.deploy.template .env.deploy
```

Required values:

```bash
DASHBOARD_DOMAIN=dashboard.cleair.ai
API_DOMAIN=api.cleair.ai
VITE_BACKEND_URL=https://api.cleair.ai
CLEAIR_AUTH_SECRET=replace-with-long-random-string
```

Create the access-code file before starting the stack:

```bash
cp web/backend/auth_codes.template.json web/backend/auth_codes.json
```

## Build and run

The production compose file uses:

- `VITE_BACKEND_URL` at frontend image build time
- `DASHBOARD_DOMAIN`, `API_DOMAIN`, and `CLEAIR_AUTH_SECRET` at runtime

Start the stack with:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.deploy up -d --build
```

## Routing

- `https://$DASHBOARD_DOMAIN` -> frontend container
- `https://$API_DOMAIN` -> backend container

## DNS

Point both hostnames at the server running Docker and Caddy:

- `dashboard.cleair.ai` -> server IP
- `api.cleair.ai` -> server IP

## Notes

- Real domain names are not committed to the repo.
- `.env.deploy` is ignored by git.
- `web/backend/auth_codes.json` is ignored by git.
- Auth is a lightweight demo gate backed by a 6-digit code list.
- The backend remains in-memory only after login.
