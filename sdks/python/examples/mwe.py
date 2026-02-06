from __future__ import annotations

import cleair
from cleair import CleairConfig


class Agent:
    @cleair.observe(name="llm", capture_output=True)
    def run(self, user_input: str) -> str:
        with cleair.span("llm"):
            return "Hello, how can I help you?"


@cleair.observe(name="request", capture_output=True)
def main() -> None:
    result = Agent().run("hello")
    print(result)


if __name__ == "__main__":
    cleair.init(CleairConfig(service_name="my-agent", exporter="console"))
    main()
