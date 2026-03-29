from __future__ import annotations

import time
import cleair


class Agent:
    def run(self, user_input: str) -> str:
        with cleair.span("agent.plan"):
            time.sleep(0.02)

        with cleair.span("agent.tool", attributes={"tool.name": "mock_search"}):
            time.sleep(0.03)

        with cleair.span("agent.llm", attributes={"gen_ai.request.model": "unknown"}):
            time.sleep(0.05)
            return f"Echo: {user_input}"


@cleair.trace(span_name="agent.request")
def main() -> None:
    Agent().run("hello")


if __name__ == "__main__":
    # cleair.init(service_name="my-agent", cleair_api_key="<key>")
    cleair.init(cleair.CleairConfig(service_name="my-agent", exporter="console"))
    main()
