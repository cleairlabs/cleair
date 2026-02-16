from __future__ import annotations

import sys
import threading
from collections import defaultdict
from collections.abc import Iterable

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult


class CleairConsoleSpanExporter(SpanExporter):
    """Pretty terminal span exporter for finite local workflows.

    This exporter is optimized for developer-facing terminal output in scripts
    and short-lived runs. It buffers spans per trace to build readable trees.

    A trace is printed when one of these conditions is true:
    1. A local root span is present (`span.parent is None`).
    2. A span with a remote parent is present (`span.parent.is_remote`).
    3. The trace was already printed before and new continuation spans arrive.

    If none of these conditions is met, spans stay buffered until `force_flush()`
    or `shutdown()`.

    Limitation:
    - `_emitted_trace_ids` grows with each printed trace and is not evicted.
      This is acceptable for finite workflows where the process exits, but it is
      not intended for long-running high-throughput services.
    """
    def __init__(self, *, use_rich: bool = True, stream: bool = False) -> None:
        self.use_rich = use_rich
        self.stream = stream
        self._pending_spans_by_trace_id: dict[int, list[ReadableSpan]] = defaultdict(list)
        self._emitted_trace_ids: set[int] = set()
        self._pending_spans_lock = threading.Lock()


    def export(self, spans: Iterable[ReadableSpan]) -> SpanExportResult:
        span_list = list(spans)
        if not span_list: return SpanExportResult.SUCCESS
        if self.stream:
            self._emit_traces(self._group_spans_by_trace_id(span_list))
            return SpanExportResult.SUCCESS

        ready_spans_by_trace_id: dict[int, list[ReadableSpan]] = {}
        touched_trace_ids: set[int] = set()
        with self._pending_spans_lock:
            for span in span_list:
                trace_id = span.context.trace_id
                touched_trace_ids.add(trace_id)
                self._pending_spans_by_trace_id[trace_id].append(span)
            for trace_id in sorted(touched_trace_ids):
                trace_spans = self._pending_spans_by_trace_id.get(trace_id, [])
                if self._should_emit_trace(trace_id, trace_spans):
                    ready_spans_by_trace_id[trace_id] = trace_spans
                    del self._pending_spans_by_trace_id[trace_id]
        self._emit_traces(ready_spans_by_trace_id)
        return SpanExportResult.SUCCESS


    def _group_spans_by_trace_id(self, spans: list[ReadableSpan]) -> dict[int, list[ReadableSpan]]:
        spans_by_trace_id: dict[int, list[ReadableSpan]] = defaultdict(list)
        for span in spans:
            spans_by_trace_id[span.context.trace_id].append(span)
        return dict(spans_by_trace_id)


    def _emit_traces(self, spans_by_trace_id: dict[int, list[ReadableSpan]]) -> None:
        if not spans_by_trace_id: return
        rich_console = self._resolve_rich_console()
        for trace_id in sorted(spans_by_trace_id):
            trace_spans = spans_by_trace_id[trace_id]
            if rich_console is not None:
                self._print_trace_with_rich(rich_console, trace_id, trace_spans)
            else:
                self._print_trace_plain(trace_id, trace_spans)
            if not self.stream: self._emitted_trace_ids.add(trace_id)


    def _has_root_span(self, spans: list[ReadableSpan]) -> bool:
        for span in spans:
            if span.parent is None: return True
        return False


    def _has_remote_parent_span(self, spans: list[ReadableSpan]) -> bool:
        for span in spans:
            if span.parent is not None and span.parent.is_remote: return True
        return False


    def _should_emit_trace(self, trace_id: int, spans: list[ReadableSpan]) -> bool:
        if trace_id in self._emitted_trace_ids: return True
        if self._has_root_span(spans): return True
        if self._has_remote_parent_span(spans): return True
        return False


    def _resolve_rich_console(self):
        if not self.use_rich      : return None
        if not sys.stdout.isatty(): return None
        try: 
            from rich.console import Console
        except ImportError:
            return None
        return Console()


    def force_flush(self, timeout_millis: int = 30000) -> bool:
        with self._pending_spans_lock:
            spans_by_trace_id = dict(self._pending_spans_by_trace_id)
            self._pending_spans_by_trace_id.clear()
        self._emit_traces(spans_by_trace_id)
        return True


    def shutdown(self) -> None:
        self.force_flush()
        return None


    def _build_children_by_parent_id(
        self,
        spans: list[ReadableSpan],
    ) -> dict[int | None, list[ReadableSpan]]:
        spans_by_span_id = {span.context.span_id: span for span in spans}
        children_by_parent_id: dict[int | None, list[ReadableSpan]] = defaultdict(list)

        for span in spans:
            parent_span_id = span.parent.span_id if span.parent else None
            if parent_span_id is None or parent_span_id in spans_by_span_id:
                children_by_parent_id[parent_span_id].append(span)
            else:
                children_by_parent_id[None].append(span)
        for child_spans in children_by_parent_id.values():
            child_spans.sort(key=lambda child_span: child_span.start_time)

        return children_by_parent_id


    def _print_trace_plain(self, trace_id: int, spans: list[ReadableSpan]) -> None:
        children_by_parent_id = self._build_children_by_parent_id(spans)
        trace_duration_ms = self._compute_trace_duration_ms(spans)
        print(f"trace={trace_id:032x} spans={len(spans)} duration_ms={trace_duration_ms:.3f}")
        self._print_children(children_by_parent_id, parent_span_id=None, depth=0)


    def _print_children(
        self,
        children_by_parent_id: dict[int | None, list[ReadableSpan]],
        *,
        parent_span_id: int | None,
        depth: int,
    ) -> None:
        for span in children_by_parent_id.get(parent_span_id, []):
            print(f"{'  ' * depth}- {self._format_span_line(span)}")
            self._print_children(
                children_by_parent_id,
                parent_span_id=span.context.span_id,
                depth=depth + 1,
            )


    def _format_span_line(self, span: ReadableSpan) -> str:
        duration_ms = (span.end_time - span.start_time) / 1_000_000.0
        status_code_name = span.status.status_code.name
        event_count = len(span.events)
        key_attributes = self._format_key_attributes(span)
        status_fragment = f" status={status_code_name}" if status_code_name == "ERROR" else ""
        return (
            f"{span.name} [{span.context.span_id:016x}] {duration_ms:.3f}ms "
            f"events={event_count}{status_fragment}{key_attributes}"
        )


    def _format_key_attributes(self, span: ReadableSpan) -> str:
        selected_key_attributes = self._get_selected_key_attributes(span)
        selected_attributes = [
            f"{attribute_key}={attribute_value}"
            for attribute_key, attribute_value in selected_key_attributes
        ]
        if not selected_attributes:
            return ""
        return " " + " ".join(selected_attributes)

    def _get_selected_key_attributes(self, span: ReadableSpan) -> list[tuple[str, str | int | float | bool]]:
        interesting_attribute_keys = ("gen_ai.request.model", "session.id")
        selected_key_attributes: list[tuple[str, str | int | float | bool]] = []
        for attribute_key in interesting_attribute_keys:
            attribute_value = span.attributes.get(attribute_key)
            if attribute_value is not None:
                selected_key_attributes.append((attribute_key, attribute_value))
        return selected_key_attributes


    def _compute_trace_duration_ms(self, spans: list[ReadableSpan]) -> float:
        first_start_time = min(span.start_time for span in spans)
        last_end_time = max(span.end_time for span in spans)
        return (last_end_time - first_start_time) / 1_000_000.0


    def _print_trace_with_rich(self, console, trace_id: int, spans: list[ReadableSpan]) -> None:
        from rich.tree import Tree

        children_by_parent_id = self._build_children_by_parent_id(spans)
        trace_duration_ms = self._compute_trace_duration_ms(spans)
        root_tree = Tree(
            f"[bold cyan]trace[/] [white]{trace_id:032x}[/] "
            f"[dim]spans={len(spans)} duration_ms={trace_duration_ms:.3f}[/]"
        )
        self._append_children_to_tree(root_tree, children_by_parent_id, parent_span_id=None)
        console.print(root_tree)


    def _append_children_to_tree(
        self,
        parent_tree,
        children_by_parent_id: dict[int | None, list[ReadableSpan]],
        *,
        parent_span_id: int | None,
    ) -> None:
        for span in children_by_parent_id.get(parent_span_id, []):
            span_tree = parent_tree.add(self._format_span_rich_label(span))
            self._append_key_attributes_to_tree(span_tree, span)
            self._append_children_to_tree(span_tree, children_by_parent_id, parent_span_id=span.context.span_id)


    def _format_span_rich_label(self, span: ReadableSpan) -> str:
        duration_ms = (span.end_time - span.start_time) / 1_000_000.0
        status_code_name = span.status.status_code.name
        rich_status_fragment = ""
        if status_code_name == "ERROR": rich_status_fragment = " [red]status=ERROR[/]"
        return (
            f"[bold]{span.name}[/] "
            f"[dim]{duration_ms:.3f}ms[/] "
            f"[dim]events={len(span.events)}[/]"
            f"{rich_status_fragment}"
        )

    def _append_key_attributes_to_tree(self, span_tree, span: ReadableSpan) -> None:
        selected_key_attributes = self._get_selected_key_attributes(span)
        if selected_key_attributes: span_tree.add(f"[yellow]ATTRIBUTES[/]")
        for attribute_key, attribute_value in selected_key_attributes:
            span_tree.add(f"[yellow] * {attribute_key}={attribute_value}[/]")
