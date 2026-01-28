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
```
