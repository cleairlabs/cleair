# cleAIr - Python SDK


## Install
Clone the repository, then install with:

```bash
pip install -e .
```

or if you are in the project root:

```bash
pip install -e sdks/python
```

## Quickstart

```python
from cleair import observe

@observe(name="story", capture_output=True)
def story() -> None:
    ...

@observe()
def main() -> None:
    story()
```


```python
import cleair

cleair.init(service_name="my-agent", cleair_api_key="<key>")

@cleair.observe(name="agent.request")
def main() -> None:
    with cleair.span("agent.plan"):
        ...
    with cleair.span("agent.llm", attributes={"gen_ai.request.model": "gpt-4o"}):
        ...
```

```python
with cleair.start_run("agent.run", agent_id="agent-7", batch_id="batch-42"):
    ...
```

Use `metadata={...}` only for arbitrary extra fields that do not have a first-class parameter.

By default, cleAIr uses `https://api.cleair.ai`, exports OTLP traces to
`/v1/traces`, and sends best-effort live span starts to `/v1/live`. OTLP remains
the authoritative trace path. The simplest setup is:

```python
cleair.init(service_name="my-agent", cleair_api_key="<key>")
```

If you skip `cleair.init(...)`, cleAIr reads `CLEAIR_SERVICE_NAME`,
`CLEAIR_BASE_URL`, `CLEAIR_API_KEY`, and `CLEAIR_ENABLED` from the environment
when tracing starts.

## Node types

Control the icon and color shown in the web UI via the `cleair.type` constants:

```python
with cleair.span("retrieve", attributes=cleair.type.SEARCH):
    ...

@cleair.observe(name="plan", as_type=cleair.type.AGENT)
def plan(): ...
```

| Constant | Icon | Color |
|---|---|---|
| `cleair.type.AGENT` | sparkle | purple |
| `cleair.type.SEARCH` | magnifying glass | blue |
| `cleair.type.TOOL` | terminal `>_` | orange (default) |

## License

[GPLv3](LICENSE)
