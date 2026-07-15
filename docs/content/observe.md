# Observe functions

Use `@cleair.observe` to trace a function call.
Each observed call appears as a step in the cleair trace UI.

## Basic usage

```python
import cleair

cleair.init(service_name="My agent", cleair_api_key="<api-key>")

@cleair.observe(name="research")
def research(topic: str) -> str:
    return f"Research result for {topic}"

print(research("quantum computing"))
```

The `name` is the label shown for the step in the trace.

`@cleair.observe` can be used on sync and async functions.

```python
@cleair.observe(name="research", capture_input=True)
async def research(topic: str) -> str:
    return f"Research result for {topic}"
```

## Capture input and output

Use `capture_input=True` to capture function arguments.
Use `capture_output=True` to capture the return value.

```python
@cleair.observe(name="research", capture_input=True, capture_output=True)
def research(topic: str) -> str:
    return f"Research result for {topic}"
```

Captured input and output values appear in the selected step's Details panel.

Only enable input or output capture when the values are safe to send to cleAIr.

## Node types

Use `as_type` to control how the step is displayed in the trace.
These types are currently only used as visuals in the UI.

E.g.:
```python
@cleair.observe(name="web_search", as_type=cleair.type.SEARCH)
def web_search(query: str) -> list[str]:
    return ["example.com"]

@cleair.observe(name="call_tool", as_type=cleair.type.TOOL)
def call_tool(prompt: str) -> str:
    return "done"
```

The available types are:

| Type | Use for | UI symbol |
|---|---|---|
| `cleair.type.TRACE` | Top-level trace/root steps | Eclipse |
| `cleair.type.AGENT` | Agent steps | Robot |
| `cleair.type.INTELLIGENCE` | Model reasoning or intelligence steps | Sparkle |
| `cleair.type.SEARCH` | Search or retrieval steps | Magnifying glass |
| `cleair.type.TOOL` | Tool calls | Terminal prompt |
| `cleair.type.HUMAN` | Human input steps | Person |
