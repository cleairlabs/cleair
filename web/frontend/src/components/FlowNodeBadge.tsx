import type { ReactElement } from "react";
import { typeColors } from "../nodeTypes";
import type { FlowNodeType } from "../types";

/** Eclipse — represents a top-level trace. */
function TraceIcon() {
  return (
    <svg width="10" height="10" viewBox="0 0 10 10">
      <path fill="#000000" fillRule="evenodd" d="M9,5 A4,4,0,1,0,1,5 A4,4,0,1,0,9,5 M9.5,5 A3,3,0,1,0,3.5,5 A3,3,0,1,0,9.5,5" />
      <circle cx="5" cy="5" r="4" fill="none" stroke="#000000" strokeWidth="1" />
    </svg>
  );
}

/** Agent/robot — represents AI/agent/robot. */
function AgentIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
      <line x1="6" y1="0.2" x2="6" y2="1.7" stroke="#fff" strokeWidth="1.1" strokeLinecap="round" />
      <circle cx="6" cy="0.2" r="0.85" fill="#fff" />
      <rect x="0.3" y="1.6" width="11.4" height="10.2" rx="1.8" fill="#fff" />
      <circle cx="3.9" cy="6.4" r="1.05" fill="#000" />
      <circle cx="8.1" cy="6.4" r="1.05" fill="#000" />
    </svg>
  );
}

/** Sparkle — represents intelligence. */
function IntelligenceIcon() {
  return (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="#ffffff">
      <path d="M5 0 L6.2 3.8 L10 5 L6.2 6.2 L5 10 L3.8 6.2 L0 5 L3.8 3.8 Z" />
    </svg>
  );
}

/** Magnifying glass — represents search and retrieval. */
function SearchIcon() {
  return (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
      <circle cx="4.2" cy="4.2" r="2.8" />
      <line x1="6.2" y1="6.2" x2="9.5" y2="9.5" />
    </svg>
  );
}

/** Terminal prompt — represents function/tool execution. */
function ToolIcon() {
  return (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="1,2.5 4.5,5 1,7.5" />
      <line x1="5.5" y1="7.5" x2="9" y2="7.5" />
    </svg>
  );
}

/** Person silhouette — represents a human action. */
function HumanIcon() {
  return (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="currentColor">
      <circle cx="5" cy="2.7" r="1.8" />
      <path d="M1.8 9c0-2 1.6-3.5 3.2-3.5s3.2 1.5 3.2 3.5H1.8z" />
    </svg>
  );
}

const typeIcons: Record<FlowNodeType, () => ReactElement> = {
  trace: TraceIcon,
  agent: AgentIcon,
  intelligence: IntelligenceIcon,
  search: SearchIcon,
  tool: ToolIcon,
  human: HumanIcon,
};

export function TypeBadge({ type }: { type: FlowNodeType }) {
  const Icon = typeIcons[type];
  return (
    <span className={`type-badge type-badge-${type}`} style={{ background: typeColors[type] }}>
      <Icon />
    </span>
  );
}
