"""Claude Code OTLP span presentation for the cleAIr UI."""
from __future__ import annotations

from cleair_backend.providers.models import SpanAttributeValue, SpanPresentation


class ClaudeCodeAdapter:
    def supports(self, span_name: str) -> bool:
        return span_name.startswith("claude_code.")

    def run_metadata(self, span_name: str, span_attributes: dict[str, SpanAttributeValue]) -> dict[str, SpanAttributeValue]:
        if span_name != "claude_code.interaction" or "session.id" not in span_attributes:
            return {}
        return {"batch.id": str(span_attributes["session.id"])}

    def present(self, span_name: str, span_attributes: dict[str, SpanAttributeValue], service_name: str) -> SpanPresentation | None:
        if span_name == "claude_code.interaction":
            return SpanPresentation(label="Claude Code", node_type="agent", subtitle="Interaction")
        if span_name == "claude_code.llm_request":
            model_name = str(span_attributes.get("gen_ai.request.model", span_attributes.get("model", "Unknown model")))
            return SpanPresentation(label="LLM request", node_type="intelligence", subtitle=model_name)
        if span_name == "claude_code.tool":
            tool_details = []
            if "full_command" in span_attributes:
                tool_details.append(f"Command: {span_attributes['full_command']}")
            if "file_path" in span_attributes:
                tool_details.append(f"File: {span_attributes['file_path']}")
            return SpanPresentation(label=str(span_attributes.get("tool_name", "Tool")),
                                    node_type="tool",
                                    subtitle="Claude Code",
                                    input_value="\n".join(tool_details) or None,
                                    output_event_name="tool.output",
                                    output_attribute_name="output")
        if span_name == "claude_code.tool.blocked_on_user":
            return SpanPresentation(label="Permission decision", node_type="human", subtitle="Claude Code")
        if span_name == "claude_code.tool.execution":
            return SpanPresentation(label="Execution", node_type="tool", subtitle="Claude Code")
        if span_name == "claude_code.hook":
            return SpanPresentation(label="Hook", node_type="tool", subtitle="Claude Code")
        return None
