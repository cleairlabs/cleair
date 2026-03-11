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
```

## Build and run

The production compose file uses:

- `VITE_BACKEND_URL` at frontend image build time
- `DASHBOARD_DOMAIN` and `API_DOMAIN` at Caddy runtime

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
- There is no proxy-level login in this setup.
- The backend remains in-memory only.
