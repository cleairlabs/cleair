# cleAIr - Python SDK


## Install
Clone the repository, then install with:

```bash
pip install -e .
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

cleair.init(cleair.CleairConfig(service_name="my-agent", exporter="console"))

@cleair.observe(name="agent.request")
def main() -> None:
    with cleair.span("agent.plan"):
        ...
    with cleair.span("agent.llm", attributes={"gen_ai.request.model": "gpt-4o"}):
        ...
```

## License

[GPLv3](LICENSE)
