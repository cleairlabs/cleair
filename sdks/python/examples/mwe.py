from __future__ import annotations

import time

import cleair


@cleair.observe(name="web_search", capture_output=True, as_type=cleair.type.SEARCH)
def web_search(query: str) -> list[str]:
    time.sleep(0.7)
    return ["en.wikipedia.org/quantum", "arxiv.org/abs/2401", "nature.com/articles/q42"]


@cleair.observe(name="fetch_page", as_type=cleair.type.SEARCH)
def fetch_page(url: str) -> str:
    time.sleep(0.3)
    return f"<html>content from {url}</html>"


@cleair.observe(name="validate_len", as_type=cleair.type.TOOL)
def validate_len(string: str) -> bool:
    return len(string) < 1_000


@cleair.observe(name="call_llm", capture_output=True, as_type=cleair.type.TOOL)
def call_llm(prompt: str) -> str:
    time.sleep(1.1)
    output = "Quantum computing uses qubits to perform calculations exponentially faster than classical bits."
    return output if validate_len(output) else "Too long"


@cleair.observe(name="research", as_type=cleair.type.AGENT)
def research(topic: str) -> str:
    urls = web_search(topic)
    pages = [fetch_page(url) for url in urls[:2]]
    return call_llm(f"Summarise based on: {pages}")


@cleair.observe(name="ask_human", capture_output=True, as_type=cleair.type.HUMAN)
def ask_human() -> bool:
    answer = input("Should we continue? (y/n) ")
    return answer.lower() == "y"


@cleair.observe(name="main", as_type=cleair.type.TRACE)
def main() -> None:
    for topic in ["quantum computing", "large language models"]:
        answer = research(topic)
        print(f"[{topic}] {answer}")
        ask_human()


if __name__ == "__main__":
    cleair.init(base_url="http://localhost:8000", cleair_api_key="<api-key>")
    main()
