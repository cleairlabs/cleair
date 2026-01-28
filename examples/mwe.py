from __future__ import annotations

import cleair
from cleair import CleairConfig


class Agent:
    def run(self, user_input: str) -> str:
        with cleair.span("agent.llm"):
            return "Hello, how can I help you?"


@cleair.trace(span_name="agent.request")
def main() -> None:
    result = Agent().run("hello")
    print(result)


if __name__ == "__main__":
    cleair.init(CleairConfig(service_name="my-agent", exporter="console"))
    main()