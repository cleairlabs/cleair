"""Node type constants for the cleAIr web UI.

Usage:
    with cleair.span("retrieve", attributes=cleair.type.SEARCH):
        ...

    @cleair.observe(name="plan", as_type=cleair.type.AGENT)
    def plan(): ...
"""

_Attrs = dict[str, str | int | float | bool]

TRACE:        _Attrs = {"cleair.type": "trace"}
AGENT:        _Attrs = {"cleair.type": "agent"}
INTELLIGENCE: _Attrs = {"cleair.type": "intelligence"}
HUMAN:        _Attrs = {"cleair.type": "human"}
SEARCH:       _Attrs = {"cleair.type": "search"}
TOOL:         _Attrs = {"cleair.type": "tool"}
