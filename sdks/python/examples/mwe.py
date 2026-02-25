from __future__ import annotations
import time
import cleair
from cleair import CleairConfig


class Agent:
    @cleair.observe(name="run()", capture_output=True, attributes=cleair.kind.AGENT)
    def run(self, user_input: str) -> str:
        with cleair.span("llm", attributes=cleair.kind.TOOL):
            time.sleep(1) # Sleep in order to make streaming visible when using terminal_stream=True
            if user_input == "boom":
                raise RuntimeError("synthetic llm failure")
            return "Hello, how can I help you?"


@cleair.observe(name="main()", capture_output=True, attributes=cleair.kind.AGENT)
def main() -> None:
    for _ in range(2):
        result = Agent().run("hello")
        if VERBOSE: print(f"AGENT SAYS: {result}")

    if VERBOSE: print("SENDING THE BOOM...")
    try:
        Agent().run("boom")
    except RuntimeError:
        if VERBOSE: print("recovered from synthetic error")

    time.sleep(4)


if __name__ == "__main__":
    cleair.init(CleairConfig(service_name="my-agent", exporter="cleair_http"))
    main()
