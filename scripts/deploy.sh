#!/usr/bin/env bash

set -euo pipefail

repo_dir="${REPO_DIR:-/opt/cleair}"
deploy_branch="${DEPLOY_BRANCH:-main}"
env_file="${ENV_FILE:-.env.deploy}"
compose_file="${COMPOSE_FILE:-docker-compose.prod.yml}"

cd "${repo_dir}"

git fetch origin "${deploy_branch}"
git checkout "${deploy_branch}"
git pull --ff-only origin "${deploy_branch}"

docker compose -f "${compose_file}" --env-file "${env_file}" up -d --build
