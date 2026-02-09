#!/usr/bin/env bash
set -euo pipefail

PYTHONPATH=services/gateway/src python -m celery -A gateway.queue:celery_app worker --loglevel INFO
