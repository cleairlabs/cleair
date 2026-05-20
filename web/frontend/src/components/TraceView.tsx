import type { ComponentType } from "react";
import { TraceTree } from "./TraceTree";
import type { TraceViewName, TraceViewProps } from "./traceViewTypes";

const traceViewRenderers: Record<TraceViewName, ComponentType<TraceViewProps>> = {
  tree: TraceTree,
};

type TraceViewComponentProps = TraceViewProps & {
  view: TraceViewName;
};

export function TraceView({ view, ...traceViewProps }: TraceViewComponentProps) {
  const TraceViewRenderer = traceViewRenderers[view];
  return <TraceViewRenderer {...traceViewProps} />;
}
