# Claude & Codex integrations

cleAIr receives OpenTelemetry (OTLP) traces at its hosted trace endpoint, `https://api.cleair.ai/v1/traces`. An integration may use the generic OTLP span view or a provider adapter that turns provider-specific span names and attributes into cleAIr node labels and types.




## Claude Code
Claude Code can export native OTLP traces. cleAIr maps its documented `claude_code.*` spans into the trace UI:

- interactions become `cleair.type.agent` steps;
- model requests become `cleair.type.intelligence` steps;
- tools, hook executions, and tool executions become `cleair.type.tool` steps;
- permission waits become `cleair.type.human` steps.


### Run Claude Code with cleAIr
Create `claude-cleair.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

read -r -s -p "Cleair API key: " CLEAIR_API_KEY
printf '\n'

export CLAUDE_CODE_ENABLE_TELEMETRY=1
export CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1
export OTEL_TRACES_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_TRACES_PROTOCOL=http/protobuf
export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=https://api.cleair.ai/v1/traces
export OTEL_EXPORTER_OTLP_HEADERS="Authorization=Bearer ${CLEAIR_API_KEY}"
export OTEL_LOG_TOOL_DETAILS=1
export OTEL_LOG_USER_PROMPTS=1
export OTEL_LOG_TOOL_CONTENT=1

exec claude "$@"
```

Copy the cleAIr API key from the **KEY** button in the web UI, then run:

```bash
bash claude-cleair.sh
```

This script sends prompts and tool details and content to cleAIr. Use it only when sending that data to cleAIr is acceptable for your environment.

`OTEL_LOG_TOOL_DETAILS=1` includes Bash commands and file paths for Read, Edit, and Write tools. `OTEL_LOG_TOOL_CONTENT=1` includes tool input and output content.

For the current Claude Code telemetry configuration and privacy controls, see the [Claude Code monitoring documentation](https://code.claude.com/docs/en/monitoring-usage).




## Codex
Codex can export OpenTelemetry logs and metrics for conversations, API requests, tool activity, approvals, and token usage.
cleAIr currently accepts OTLP traces only, so Codex cannot yet be displayed in cleAIr directly.

This differs from Claude Code: Codex's documented export is structured logs and metrics, while Claude Code can export the trace hierarchy that cleAIr consumes.
A future Codex integration requires an OTLP log ingestion and mapping layer; do not point Codex's log exporter at cleAIr's `/v1/traces` endpoint.

For Codex's current event types and telemetry configuration, see the [Codex observability documentation](https://learn.chatgpt.com/docs/config-file/config-advanced#observability-and-telemetry).
