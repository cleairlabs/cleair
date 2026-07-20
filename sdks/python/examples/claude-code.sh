#!/usr/bin/env bash
set -euo pipefail

read -r -s -p "Cleair API key: " CLEAIR_API_KEY
printf '\n'

export CLAUDE_CODE_ENABLE_TELEMETRY=1
export CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1
export OTEL_TRACES_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_TRACES_PROTOCOL=http/protobuf
# export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=https://api.cleair.ai/v1/traces
export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://localhost:8000/v1/traces
export OTEL_EXPORTER_OTLP_HEADERS="Authorization=Bearer ${CLEAIR_API_KEY}"
export OTEL_LOG_TOOL_DETAILS=1
export OTEL_LOG_USER_PROMPTS=1
export OTEL_LOG_TOOL_CONTENT=1

exec claude "$@"
