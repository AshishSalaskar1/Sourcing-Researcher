from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any, Literal

from pydantic import BaseModel, Field


def _json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    try:
        return json.loads(json.dumps(value, default=str))
    except TypeError:
        return str(value)


def summarize_value(value: Any, *, limit: int = 420) -> str | None:
    safe_value = _json_safe(value)
    if safe_value is None:
        return None
    if isinstance(safe_value, str):
        text = safe_value.strip()
    else:
        text = json.dumps(safe_value, indent=2, ensure_ascii=True)
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3].rstrip()}..."


class DebugToolCall(BaseModel):
    id: str
    label: str
    args_summary: str | None = None
    args_detail: str | None = None
    output_summary: str | None = None
    output_detail: str | None = None


class DebugNode(BaseModel):
    id: str
    label: str
    kind: Literal["agent", "tool"]
    depth: int = Field(ge=0, default=0)
    order: int = Field(ge=0, default=0)
    parent_id: str | None = None
    input_summary: str | None = None
    input_detail: str | None = None
    output_summary: str | None = None
    output_detail: str | None = None
    output_data: Any | None = None
    duration_seconds: float | None = None
    tool_calls: list[DebugToolCall] = Field(default_factory=list)


class DebugEdge(BaseModel):
    source: str
    target: str
    label: str | None = None


class DebugTrace(BaseModel):
    root_node_id: str
    nodes: list[DebugNode] = Field(default_factory=list)
    edges: list[DebugEdge] = Field(default_factory=list)


def collect_tool_calls(agent_result: Any) -> list[DebugToolCall]:
    calls_by_id: dict[str, DebugToolCall] = {}
    ordered_calls: list[DebugToolCall] = []

    for message in agent_result.all_messages():
        for part in message.parts:
            tool_name = getattr(part, "tool_name", None)
            tool_call_id = getattr(part, "tool_call_id", None)
            part_kind = getattr(part, "part_kind", None)
            if not tool_name or tool_name == "final_result":
                continue

            if part_kind in {"tool-call", "builtin-tool-call"}:
                call = DebugToolCall(
                    id=tool_call_id or f"{tool_name}-{len(ordered_calls)}",
                    label=tool_name,
                    args_summary=summarize_value(getattr(part, "args", None), limit=240),
                    args_detail=summarize_value(getattr(part, "args", None), limit=20_000),
                )
                calls_by_id[call.id] = call
                ordered_calls.append(call)
                continue

            if part_kind not in {"tool-return", "builtin-tool-return"}:
                continue

            if tool_call_id and tool_call_id in calls_by_id:
                calls_by_id[tool_call_id].output_summary = summarize_value(
                    getattr(part, "content", None), limit=320
                )
                calls_by_id[tool_call_id].output_detail = summarize_value(
                    getattr(part, "content", None), limit=20_000
                )
                continue

            ordered_calls.append(
                DebugToolCall(
                    id=tool_call_id or f"{tool_name}-{len(ordered_calls)}",
                    label=tool_name,
                    output_summary=summarize_value(getattr(part, "content", None), limit=320),
                    output_detail=summarize_value(getattr(part, "content", None), limit=20_000),
                )
            )

    return ordered_calls


@dataclass
class DebugTraceBuilder:
    prompt: str
    root_node_id: str = "orchestrator"
    nodes: list[DebugNode] = field(default_factory=list)
    edges: list[DebugEdge] = field(default_factory=list)
    _order: int = 0

    def __post_init__(self) -> None:
        self.nodes.append(
            DebugNode(
                id=self.root_node_id,
                label="Orchestrator",
                kind="agent",
                depth=0,
                order=self._next_order(),
                input_summary=summarize_value(self.prompt, limit=280),
                input_detail=summarize_value(self.prompt, limit=20_000),
            )
        )

    def _next_order(self) -> int:
        current = self._order
        self._order += 1
        return current

    def record_agent_run(
        self,
        *,
        node_id: str,
        label: str,
        edge_label: str,
        input_summary: str,
        output_data: Any,
        duration_seconds: float,
        tool_calls: list[DebugToolCall],
    ) -> None:
        self.nodes.append(
            DebugNode(
                id=node_id,
                label=label,
                kind="agent",
                depth=1,
                order=self._next_order(),
                parent_id=self.root_node_id,
                input_summary=summarize_value(input_summary, limit=280),
                input_detail=summarize_value(input_summary, limit=20_000),
                output_summary=summarize_value(output_data, limit=420),
                output_detail=summarize_value(output_data, limit=20_000),
                output_data=_json_safe(output_data),
                duration_seconds=round(duration_seconds, 2),
                tool_calls=tool_calls,
            )
        )
        self.edges.append(DebugEdge(source=self.root_node_id, target=node_id, label=edge_label))

        for tool_call in tool_calls:
            tool_node_id = f"{node_id}-{tool_call.id}"
            self.nodes.append(
                DebugNode(
                    id=tool_node_id,
                    label=tool_call.label,
                    kind="tool",
                    depth=2,
                    order=self._next_order(),
                    parent_id=node_id,
                    input_summary=tool_call.args_summary,
                    input_detail=tool_call.args_detail,
                    output_summary=tool_call.output_summary,
                    output_detail=tool_call.output_detail,
                )
            )
            self.edges.append(DebugEdge(source=node_id, target=tool_node_id, label="tool call"))

    def set_root_output(self, output_data: Any) -> None:
        for node in self.nodes:
            if node.id != self.root_node_id:
                continue
            node.output_summary = summarize_value(output_data, limit=420)
            node.output_detail = summarize_value(output_data, limit=20_000)
            node.output_data = _json_safe(output_data)
            return

    def build(self) -> DebugTrace:
        return DebugTrace(root_node_id=self.root_node_id, nodes=self.nodes, edges=self.edges)
