# cleAIr


Clone the repository, then install with:
## Install
```bash
pip install -e .
```

## Quickstart
```python
import cleair

cleair.init(CleairConfig(service_name="my-agent", exporter="console"))

with cleair.span("agent.request"):
    ...

@cleair.observe()
def main() -> None:
    with cleair.span("agent.request"):
        ...
```

```python
from cleair import observe

@observe()
def story():
    ...

@observe()
def main():
    ...
```
