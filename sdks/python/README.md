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

cleair.init(cleair.CleairConfig(service_name="my-agent", exporter="terminal"))

@cleair.observe(name="agent.request")
def main() -> None:
    with cleair.span("agent.plan"):
        ...
    with cleair.span("agent.llm", attributes={"gen_ai.request.model": "gpt-4o"}):
        ...
```

Available exporters:
- `otlp_http` (default)
- `console` (OpenTelemetry JSON output)
- `terminal` (cleair tree-style terminal output, uses `rich` when installed and TTY is available)

Install rich terminal rendering:

```bash
pip install -e ".[terminal]"
```

## License

[GPLv3](LICENSE)
