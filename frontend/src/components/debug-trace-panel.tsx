import { Bot, Bug, Clock3, GitBranch, Wrench, X } from "lucide-react";
import { useMemo, useState } from "react";

import type { DebugNode, DebugTrace } from "../types";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";

type DebugTracePanelProps = {
  trace: DebugTrace;
  onClose: () => void;
};

function formatJson(value: unknown) {
  return JSON.stringify(value, null, 2);
}

function nodeIcon(node: DebugNode) {
  return node.kind === "tool" ? <Wrench size={16} /> : <Bot size={16} />;
}

function nodeMeta(node: DebugNode) {
  if (node.kind === "tool") {
    return "Tool";
  }

  if (node.duration_seconds !== undefined && node.duration_seconds !== null) {
    return `${node.duration_seconds.toFixed(2)}s`;
  }

  return "Agent";
}

function nodePreview(node: DebugNode) {
  return node.output_summary ?? node.input_summary ?? "No details captured.";
}

type GraphNodeButtonProps = {
  node: DebugNode;
  selected: boolean;
  onSelect: () => void;
};

function GraphNodeButton({ node, selected, onSelect }: GraphNodeButtonProps) {
  return (
    <button
      type="button"
      className={`debug-graph-node ${selected ? "debug-graph-node-selected" : ""}`}
      onClick={onSelect}
    >
      <div className={`debug-node-icon ${node.kind === "agent" ? "debug-node-icon-agent" : ""}`}>
        {nodeIcon(node)}
      </div>
      <div className="debug-graph-node-copy">
        <div className="debug-graph-node-title">
          <span>{node.label}</span>
          <Badge>{nodeMeta(node)}</Badge>
        </div>
        <p className="debug-graph-node-preview">{nodePreview(node)}</p>
      </div>
    </button>
  );
}

export function DebugTracePanel({ trace, onClose }: DebugTracePanelProps) {
  const rootNode = trace.nodes.find((node) => node.id === trace.root_node_id) ?? null;
  const agentNodes = useMemo(
    () =>
      trace.nodes
        .filter((node) => node.kind === "agent" && node.id !== trace.root_node_id)
        .sort((left, right) => left.order - right.order),
    [trace],
  );

  const nodesById = useMemo(
    () => new Map(trace.nodes.map((node) => [node.id, node])),
    [trace.nodes],
  );

  const toolNodesByParent = useMemo(() => {
    const groups = new Map<string, DebugNode[]>();
    trace.nodes
      .filter((node) => node.kind === "tool" && node.parent_id)
      .sort((left, right) => left.order - right.order)
      .forEach((node) => {
        const parentId = node.parent_id ?? "";
        const bucket = groups.get(parentId) ?? [];
        bucket.push(node);
        groups.set(parentId, bucket);
      });
    return groups;
  }, [trace.nodes]);

  const [selectedNodeId, setSelectedNodeId] = useState(rootNode?.id ?? "");
  const selectedNode = nodesById.get(selectedNodeId) ?? rootNode;
  const selectedParent = selectedNode?.parent_id ? nodesById.get(selectedNode.parent_id) : null;
  const selectedChildTools = selectedNode ? toolNodesByParent.get(selectedNode.id) ?? [] : [];

  return (
    <div className="debug-modal-overlay" onClick={onClose} role="presentation">
      <div
        className="debug-modal"
        onClick={(event) => event.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="Agent debug graph"
      >
        <div className="debug-modal-header">
          <div className="section-heading">
            <Bug size={18} />
            <div>
              <h2 className="card-title">Execution debug graph</h2>
              <p className="card-description">
                Click any node to inspect the orchestrator, subagents, tools, and outputs.
              </p>
            </div>
          </div>
          <Button variant="ghost" type="button" onClick={onClose} aria-label="Close debug graph">
            <X size={16} />
          </Button>
        </div>

        <div className="debug-scroll">
          <div className="debug-layout">
            <Card className="debug-graph-card">
              <CardHeader>
                <CardTitle>Agent graph</CardTitle>
                <CardDescription>
                  Main agent at the top, specialist agents in the middle, and tool calls below.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="debug-graph-stage">
                  {rootNode && (
                    <div className="debug-graph-root">
                      <GraphNodeButton
                        node={rootNode}
                        selected={selectedNode?.id === rootNode.id}
                        onSelect={() => setSelectedNodeId(rootNode.id)}
                      />
                    </div>
                  )}

                  {agentNodes.length > 0 && <div className="debug-root-link" aria-hidden="true" />}

                  <div
                    className="debug-agent-columns"
                    style={{
                      gridTemplateColumns: `repeat(${Math.max(agentNodes.length, 1)}, minmax(220px, 1fr))`,
                    }}
                  >
                    {agentNodes.map((agentNode) => {
                      const toolNodes = toolNodesByParent.get(agentNode.id) ?? [];

                      return (
                        <div className="debug-agent-column" key={agentNode.id}>
                          <div className="debug-column-link" aria-hidden="true" />
                          <GraphNodeButton
                            node={agentNode}
                            selected={selectedNode?.id === agentNode.id}
                            onSelect={() => setSelectedNodeId(agentNode.id)}
                          />

                          {toolNodes.length > 0 && (
                            <div className="debug-tool-column">
                              {toolNodes.map((toolNode) => (
                                <div className="debug-tool-entry" key={toolNode.id}>
                                  <div className="debug-tool-link" aria-hidden="true" />
                                  <GraphNodeButton
                                    node={toolNode}
                                    selected={selectedNode?.id === toolNode.id}
                                    onSelect={() => setSelectedNodeId(toolNode.id)}
                                  />
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="debug-detail-card">
              <CardHeader>
                <div className="debug-node-heading">
                  <div
                    className={`debug-node-icon ${
                      selectedNode?.kind === "agent" ? "debug-node-icon-agent" : ""
                    }`}
                  >
                    {selectedNode ? nodeIcon(selectedNode) : <GitBranch size={16} />}
                  </div>
                  <div>
                    <CardTitle>{selectedNode?.label ?? "No node selected"}</CardTitle>
                    <CardDescription>
                      {selectedNode?.kind === "tool" ? "Tool call details" : "Agent details"}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="stack">
                {selectedNode && (
                  <>
                    <div className="tag-list">
                      <Badge>{selectedNode.kind}</Badge>
                      {selectedParent && <Badge>Parent: {selectedParent.label}</Badge>}
                      {selectedNode.duration_seconds !== undefined &&
                        selectedNode.duration_seconds !== null && (
                          <Badge>
                            <Clock3 size={12} />
                            {selectedNode.duration_seconds.toFixed(2)}s
                          </Badge>
                        )}
                    </div>

                    {selectedNode.input_detail && (
                      <details className="debug-details" open>
                        <summary>Input</summary>
                        <pre className="debug-code-block">{selectedNode.input_detail}</pre>
                      </details>
                    )}

                    {selectedNode.output_detail && (
                      <details className="debug-details" open>
                        <summary>Output</summary>
                        <pre className="debug-code-block">{selectedNode.output_detail}</pre>
                      </details>
                    )}

                    {selectedNode.output_data !== undefined && selectedNode.output_data !== null && (
                      <details className="debug-details">
                        <summary>Structured response</summary>
                        <pre className="debug-code-block">{formatJson(selectedNode.output_data)}</pre>
                      </details>
                    )}

                    {selectedChildTools.length > 0 && (
                      <div className="stack">
                        <p className="subsection-title">Nested tool calls</p>
                        <div className="debug-chip-list">
                          {selectedChildTools.map((toolNode) => (
                            <button
                              key={toolNode.id}
                              type="button"
                              className={`debug-chip-button ${
                                selectedNodeId === toolNode.id ? "debug-chip-button-selected" : ""
                              }`}
                              onClick={() => setSelectedNodeId(toolNode.id)}
                            >
                              <Wrench size={12} />
                              <span>{toolNode.label}</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
