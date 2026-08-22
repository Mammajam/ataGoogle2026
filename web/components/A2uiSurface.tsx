"use client";

import type { A2uiMessage, ConfirmPayload, ExtractionWidget } from "@/lib/types";

type ComponentNode = {
  id: string;
  component: string;
  [key: string]: unknown;
};

type Props = {
  messages: A2uiMessage[];
  widget: ExtractionWidget | null;
  busy?: boolean;
  onConfirm: (payload: ConfirmPayload) => void;
};

function resolveText(value: unknown, model: Record<string, unknown>): string {
  if (typeof value === "string") return value;
  if (value && typeof value === "object" && "path" in value) {
    const path = String((value as { path: string }).path).replace(/^\//, "");
    const found = model[path];
    return found == null ? "" : String(found);
  }
  return "";
}

function collectComponents(messages: A2uiMessage[]): {
  nodes: Record<string, ComponentNode>;
  model: Record<string, unknown>;
  surfaceId: string | null;
} {
  const nodes: Record<string, ComponentNode> = {};
  let model: Record<string, unknown> = {};
  let surfaceId: string | null = null;
  for (const raw of messages) {
    const msg = raw as Record<string, unknown>;
    if (msg.createSurface && typeof msg.createSurface === "object") {
      surfaceId = String((msg.createSurface as { surfaceId?: string }).surfaceId || "extraction-confirm");
    }
    if (msg.updateComponents && typeof msg.updateComponents === "object") {
      const update = msg.updateComponents as { components?: ComponentNode[] };
      for (const node of update.components || []) {
        nodes[node.id] = node;
      }
    }
    if (msg.updateDataModel && typeof msg.updateDataModel === "object") {
      const update = msg.updateDataModel as { value?: Record<string, unknown> };
      model = { ...model, ...(update.value || {}) };
    }
  }
  return { nodes, model, surfaceId };
}

function RenderNode({
  id,
  nodes,
  model,
  onAction,
}: {
  id: string;
  nodes: Record<string, ComponentNode>;
  model: Record<string, unknown>;
  onAction: (event: { name: string; context: Record<string, unknown> }) => void;
}) {
  const node = nodes[id];
  if (!node) return null;
  const kind = node.component;

  if (kind === "Card") {
    return (
      <div className="rounded-xl border border-[#c4a35a] bg-white p-4 shadow-sm">
        {typeof node.child === "string" ? (
          <RenderNode id={node.child} nodes={nodes} model={model} onAction={onAction} />
        ) : null}
      </div>
    );
  }

  if (kind === "Column") {
    const children = Array.isArray(node.children) ? (node.children as string[]) : [];
    const unique = children.filter((child, index) => children.indexOf(child) === index);
    return (
      <div className="flex flex-col gap-3">
        {unique.map((child) => (
          <RenderNode key={child} id={child} nodes={nodes} model={model} onAction={onAction} />
        ))}
      </div>
    );
  }

  if (kind === "Row") {
    const children = Array.isArray(node.children) ? (node.children as string[]) : [];
    return (
      <div className="flex flex-wrap gap-2">
        {children.map((child) => (
          <RenderNode key={child} id={child} nodes={nodes} model={model} onAction={onAction} />
        ))}
      </div>
    );
  }

  if (kind === "Text") {
    const variant = String(node.variant || "");
    const text = resolveText(node.text, model);
    if (!text) return null;
    const cls =
      variant === "h2" ? "text-xl text-[#1b4d3e]" : "sans text-sm leading-relaxed text-[#3d4a42]";
    return <p className={cls}>{text}</p>;
  }

  if (kind === "Button") {
    const action = (node.action as { event?: { name?: string; context?: Record<string, unknown> } }) || {};
    const event = action.event || { name: "click", context: {} };
    const variant = String(node.variant || "secondary");
    const labelId = typeof node.child === "string" ? node.child : "";
    const labelNode = labelId ? nodes[labelId] : null;
    const label = labelNode ? resolveText(labelNode.text, model) : "Confirm";
    const primary = variant === "primary";
    return (
      <button
        type="button"
        onClick={() =>
          onAction({
            name: String(event.name || "extraction.confirm"),
            context: (event.context || {}) as Record<string, unknown>,
          })
        }
        className={`sans rounded-lg px-3 py-2 text-left text-sm font-semibold ${
          primary
            ? "bg-[#1b4d3e] text-white hover:bg-[#14251c]"
            : "border border-[#d9d0bf] bg-[#f4efe4] text-[#14251c] hover:border-[#1b4d3e]"
        }`}
      >
        {label}
      </button>
    );
  }

  if (kind === "TextField") {
    return (
      <input
        className="sans w-full rounded border border-[#d9d0bf] px-2 py-1 text-sm"
        defaultValue={resolveText(node.value, model)}
        readOnly
      />
    );
  }

  return null;
}

export function A2uiSurface({ messages, widget, busy, onConfirm }: Props) {
  const { nodes, model } = collectComponents(messages);
  const hasTree = Boolean(nodes.root);

  const emit = (context: Record<string, unknown>) => {
    onConfirm({
      run_id: String(context.run_id || widget?.run_id || model.run_id || ""),
      line_id: String(context.line_id || widget?.line_id || "s2-grid-electricity"),
      quantity: Number(context.quantity),
      unit: String(context.unit),
    });
  };

  return (
    <section className="rounded-2xl border border-[#d9d0bf] bg-[#fbf8f1] p-5 shadow-sm">
      <h2 className="sans text-sm font-semibold tracking-wide text-[#1b4d3e] uppercase">
        Collaboration (A2UI)
      </h2>
      <p className="sans mt-1 text-xs text-[#5c6b62]">
        Widgets only for material gaps. Chat is the transcript, not the product.
      </p>
      <div className="mt-4">
        {hasTree ? (
          <RenderNode
            id="root"
            nodes={nodes}
            model={model}
            onAction={(event) => emit(event.context)}
          />
        ) : widget ? (
          <div className="rounded-xl border border-[#c4a35a] bg-white p-4">
            <p className="text-xl text-[#1b4d3e]">Extraction confirm — kWh vs MWh</p>
            <p className="sans mt-2 text-sm text-[#3d4a42]">
              Vision is 70% sure the bill is 184,200 kWh, not 184,200 MWh. Confirming
              recalculates the line.
            </p>
            <div className="mt-4 flex flex-col gap-2">
              <button
                type="button"
                disabled={busy}
                onClick={() =>
                  emit({
                    run_id: widget.run_id,
                    line_id: widget.line_id,
                    quantity: widget.recommended.quantity,
                    unit: widget.recommended.unit,
                  })
                }
                className="sans rounded-lg bg-[#1b4d3e] px-3 py-2 text-left text-sm font-semibold text-white"
              >
                Confirm {widget.recommended.quantity.toLocaleString()} {widget.recommended.unit} →{" "}
                {widget.recommended_tco2e.toFixed(3)} tCO₂e
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={() =>
                  emit({
                    run_id: widget.run_id,
                    line_id: widget.line_id,
                    quantity: widget.alternate.quantity,
                    unit: widget.alternate.unit,
                  })
                }
                className="sans rounded-lg border border-[#d9d0bf] bg-[#f4efe4] px-3 py-2 text-left text-sm font-semibold"
              >
                Use {widget.alternate.quantity.toLocaleString()} {widget.alternate.unit} →{" "}
                {widget.alternate_tco2e.toFixed(3)} tCO₂e
              </button>
            </div>
          </div>
        ) : (
          <p className="text-sm text-[#5c6b62]">No material gap. The agent is not asking.</p>
        )}
      </div>
    </section>
  );
}
