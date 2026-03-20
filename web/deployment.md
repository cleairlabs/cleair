# Web Deployment

## Host bootstrap

Alternative curl bootstrap:

For a fresh Ubuntu DigitalOcean Droplet, install `git` and run the bootstrap
script as `root`:

```bash
apt update
apt install -y git
git clone https://github.com/cleairlabs/cleair.git /opt/cleair
bash /opt/cleair/scripts/bootstrap_server.sh
```

Optional environment variables:

```bash
DEPLOY_USER=deploy TIMEZONE_NAME=Europe/Stockholm SWAP_SIZE_GB=2 bash /opt/cleair/scripts/bootstrap_server.sh
su - deploy
cd /opt/cleair/
```

The script installs base packages, Docker Engine, Docker Compose, UFW rules, swap, and a non-root deploy user with Docker and passwordless `sudo` access. 
It intentionally does not modify SSH daemon settings. 
If `/root/.ssh/authorized_keys` exists, it is copied to the deploy user to preserve login access.

Keep the production checkout in `/opt/cleair` so deployment automation can
`git fetch` and `git pull` in place before rebuilding the stack.

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
- Auth is a lightweight demo gate.
