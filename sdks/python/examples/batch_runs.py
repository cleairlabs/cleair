from __future__ import annotations

import cleair

from mwe import research


def main() -> None:
    batch_id = "batch-2"
    for agent_index in range(3):
        with cleair.start_run("agent.run", metadata={"agent.id": f"agent-{agent_index}", "batch.id": batch_id}):
            research("quantum computing")


if __name__ == "__main__":
    cleair.init(base_url="http://localhost:8000", cleair_api_key="<channel-api-key>")
    main()
