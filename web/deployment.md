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

Use `/opt/cleair` as the production directory so the deploy workflow can sync
the repo contents there before rebuilding the stack.

## GitHub Actions deploy

After bootstrapping a new server and adding the deploy SSH key, set these
GitHub Actions variables:

```bash
DEPLOY_HOST=your-server-ip-or-hostname
DEPLOY_PATH=/opt/cleair
DEPLOY_PORT=22
DEPLOY_USER=deploy
DASHBOARD_DOMAIN=dashboard.example.com
API_DOMAIN=api.example.com
DOCS_DOMAIN=docs.example.com
VITE_BACKEND_URL=https://api.example.com
```

Set these GitHub Actions secrets:

```bash
DEPLOY_SSH_KEY=<private-key-for-the-deploy-user>
CLEAIR_AUTH_SECRET=<long-random-string>
DEPLOY_AUTH_CODES_JSON={"codes":["<6-digit-code>"]}
```

Security notes:

- Keep `DASHBOARD_DOMAIN`, `API_DOMAIN`, `DOCS_DOMAIN`, and `VITE_BACKEND_URL` as GitHub
  Actions variables. They are configuration, not secrets.
- Keep `DEPLOY_SSH_KEY`, `CLEAIR_AUTH_SECRET`, and `DEPLOY_AUTH_CODES_JSON`
  as GitHub Actions secrets.
- Use a dedicated deploy key for this repo and server. Do not reuse a personal
  SSH key.
- Scope the private key to the `deploy` user on the target host and keep that
  account limited to deployment duties.
- Prefer GitHub Environment-scoped variables and secrets for production so
  deploy permissions can be restricted and reviewed.
- Never commit `.env.deploy`, `web/backend/auth_codes.json`, or private keys to
  git.

Then trigger the `Deploy` workflow from the Actions tab. The workflow:

- checks out the repo
- writes `.env.deploy` from GitHub Actions variables and secrets
- writes `web/backend/auth_codes.json` from `DEPLOY_AUTH_CODES_JSON`
- syncs the repo to the target server with `rsync`
- runs `bash scripts/deploy.sh` on the server

`.env.deploy` and `web/backend/auth_codes.json` stay untracked and are
generated fresh on every deployment.

## Build and run

The production compose file uses:

- `VITE_BACKEND_URL` at frontend image build time
- `DOCS_DOMAIN` at docs image build time and Caddy runtime
- `DASHBOARD_DOMAIN`, `API_DOMAIN`, `DOCS_DOMAIN`, and `CLEAIR_AUTH_SECRET` at runtime

The production stack contains four containers:

- `frontend`: serves the React dashboard
- `backend`: runs the FastAPI API
- `docs`: builds the MkDocs site and serves the generated files with Nginx
- `caddy`: handles HTTPS and routes each domain to the correct container

Start the stack with:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.deploy up -d --build
```

For manual server-side deploys, create `.env.deploy` and
`web/backend/auth_codes.json` with the same values before running the command.

## Routing

- `https://$DASHBOARD_DOMAIN` -> frontend container
- `https://$API_DOMAIN` -> backend container
- `https://$DOCS_DOMAIN` -> docs container

## DNS

Point all hostnames at the server running Docker and Caddy:

- `dashboard.cleair.ai` -> server IP
- `api.cleair.ai` -> server IP
- `docs.cleair.ai` -> server IP

In DigitalOcean DNS, add an `A` record with hostname `docs` and the same server IP used by `dashboard` and `api`.

## Notes

- Real domain names are not committed to the repo.
- `.env.deploy` is ignored by git.
- `web/backend/auth_codes.json` is ignored by git.
- Auth is a lightweight demo gate.
