# cleAIr

Explainable agent observability built on OpenTelemetry.

## SDKs

| Language | Path | Status |
|----------|------|--------|
| Python | [`sdks/python/`](sdks/python/) | Active |
| TS/JS | `sdks/typescript/` | Planned |


## Python SDK Example

### Install
Clone the repository, then install with:

```bash
pip install -e sdks/python
```

### Quickstart

```python
from cleair import observe

@observe(name="story", capture_output=True)
def story() -> None:
    ...

@observe()
def main() -> None:
    story()
```


## License

[GPLv3](LICENSE)
