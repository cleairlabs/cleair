"""Node kind constants for the cleAIr web UI.

Usage:
    with cleair.span("retrieve", attributes=cleair.kind.SEARCH):
        ...

    @cleair.observe(name="plan", attributes=cleair.kind.AGENT)
    def plan(): ...
"""

_Attrs = dict[str, str | int | float | bool]

TRACE: _Attrs = {"cleair.kind": "trace"}
AGENT: _Attrs = {"cleair.kind": "agent"}
SEARCH: _Attrs = {"cleair.kind": "search"}
TOOL: _Attrs = {"cleair.kind": "tool"}
