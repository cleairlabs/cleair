# cleAIr

Explainable agent observability.

## SDKs

| Language | Path | Status |
|----------|------|--------|
| Python | [`sdks/python/`](sdks/python/) | Available |
| TS/JS | `sdks/typescript/` | Planned |



## Install Python SDK

Clone the repository, then install with:

```bash
pip install -e sdks/python
```


## Python SDK Example Using the Observe Decorator

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
