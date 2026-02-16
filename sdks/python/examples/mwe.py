from __future__ import annotations

import cleair
from cleair import CleairConfig


class Agent:
    @cleair.observe(name="llm", capture_output=True)
    def run(self, user_input: str) -> str:
        with cleair.span("llm", attributes={"gen_ai.request.model": "unknown", "session.id": "session-1",},):
            if user_input == "boom":
                raise RuntimeError("synthetic llm failure")
            return "Hello, how can I help you?"


@cleair.observe(name="request", capture_output=True)
def main() -> None:
    result = Agent().run("hello")
    print(result)

    try:
        Agent().run("boom")
    except RuntimeError:
        print("recovered from synthetic error")


if __name__ == "__main__":
    cleair.init(CleairConfig(service_name="my-agent", exporter="terminal"))
    main()
