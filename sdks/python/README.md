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

By default, cleAIr uses the hosted `cleair_http` exporter and requires a
`cleair_api_key`:

```python
cleair.init(service_name="my-agent", cleair_api_key="<key>")
```

The API key must be passed to `cleair.init(...)` or included in an explicit
`CleairConfig(...)`. It is not read from environment variables.

Available exporters:
- `cleair_http` (default) — streams to the cleAIr web UI (`https://api.cleair.ai/v1/events`)
- `console` — OpenTelemetry JSON output

## Node kinds

Control the icon and color shown in the web UI via the `cleair.kind` attribute:

```python
with cleair.span("retrieve", attributes=cleair.kind.SEARCH):
    ...

@cleair.observe(name="plan", attributes=cleair.kind.AGENT)
def plan(): ...
```

| Constant | Icon | Color |
|---|---|---|
| `cleair.kind.AGENT` | sparkle | purple |
| `cleair.kind.SEARCH` | magnifying glass | blue |
| `cleair.kind.TOOL` | terminal `>_` | orange (default) |

## License

[GPLv3](LICENSE)
