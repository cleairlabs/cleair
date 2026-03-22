#!/usr/bin/env bash

set -euo pipefail

repo_dir="${REPO_DIR:-/opt/cleair}"
env_file="${ENV_FILE:-.env.deploy}"
compose_file="${COMPOSE_FILE:-docker-compose.prod.yml}"

cd "${repo_dir}"

docker compose -f "${compose_file}" --env-file "${env_file}" up -d --build
