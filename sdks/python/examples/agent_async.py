from __future__ import annotations

import asyncio
import cleair


class Agent:
    async def run(self, user_input: str) -> str:
        with cleair.span("agent.plan"):
            await asyncio.sleep(0.02)

        with cleair.span("agent.llm", attributes={"gen_ai.request.model": "unknown"}):
            await asyncio.sleep(0.05)
            return f"Echo: {user_input}"


@cleair.observe(name="agent.request")
async def main() -> None:
    await Agent().run("hello")


if __name__ == "__main__":
    cleair.init(service_name="my-agent", cleair_api_key="<key>")
    asyncio.run(main())
