# cleair
cleair - a framework for explainable agent observability


## Install
```bash
pip install cleair
```

## Quickstart
```python
import cleair

cleair.init(CleairConfig(service_name="my-agent", exporter="console"))

with cleair.span("agent.request"):
    ...
```