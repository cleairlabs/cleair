from __future__ import annotations
import time
import cleair
from cleair import CleairConfig


@cleair.observe(name="web_search", capture_output=True, attributes=cleair.kind.SEARCH)
def web_search(query: str) -> list[str]:
    time.sleep(0.7)
    return ["en.wikipedia.org/quantum", "arxiv.org/abs/2401", "nature.com/articles/q42"]


@cleair.observe(name="fetch_page", attributes=cleair.kind.SEARCH)
def fetch_page(url: str) -> str:
    time.sleep(0.3)
    return f"<html>content from {url}</html>"


@cleair.observe(name="call_llm", capture_output=True, attributes=cleair.kind.TOOL)
def call_llm(prompt: str) -> str:
    time.sleep(1.1)
    return "Quantum computing uses qubits to perform calculations exponentially faster than classical bits."


@cleair.observe(name="research", attributes=cleair.kind.AGENT)
def research(topic: str) -> str:
    urls = web_search(topic)
    pages = [fetch_page(url) for url in urls[:2]]
    return call_llm(f"Summarise based on: {pages}")


@cleair.observe(name="main", attributes=cleair.kind.TRACE)
def main() -> None:
    for topic in ["quantum computing", "large language models"]:
        answer = research(topic)
        print(f"[{topic}] {answer}")


if __name__ == "__main__":
    cleair.init(CleairConfig(service_name="research-agent", exporter="cleair_http", cleair_api_key="07c5496b9ac28ba93380e17958d44bc8"))
    main()
