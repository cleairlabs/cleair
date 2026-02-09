#!/usr/bin/env bash
set -euo pipefail

PYTHONPATH=services/gateway/src python -m uvicorn gateway.main:app --host 0.0.0.0 --port 8000
