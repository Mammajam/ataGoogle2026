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
    const create = msg.createSurface as { surfaceId?: string } | undefined;
    if (create && typeof create === "object") {
      surfaceId = String(create.surfaceId || "extraction-confirm");
    }
    const components = msg.updateComponents as { components?: ComponentNode[] } | undefined;
    if (components && typeof components === "object") {
      for (const node of components.components || []) {
        nodes[node.id] = node;
      }
    }
    const dataModel = msg.updateDataModel as { value?: Record<string, unknown> } | undefined;
    if (dataModel && typeof dataModel === "object") {
      model = { ...model, ...(dataModel.value || {}) };
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
      <div className="rounded-lg border border-border bg-background p-4 shadow-sm">
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
      variant === "h2" ? "text-xl font-semibold text-foreground" : "text-sm leading-relaxed text-muted-foreground";
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
        className={`rounded-full px-4 py-2.5 text-left text-sm font-semibold transition ${
          primary
            ? "glow-primary bg-primary text-primary-foreground shadow-sm hover:opacity-90"
            : "bg-accent text-accent-foreground hover:bg-accent/80"
        }`}
      >
        {label}
      </button>
    );
  }

  if (kind === "TextField") {
    return (
      <input
        className="w-full rounded-sm border border-border bg-input px-3 py-2 text-sm"
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
      line_id: String(context.line_id || widget?.line_id || ""),
      quantity: Number(context.quantity),
      unit: String(context.unit),
    });
  };

  return (
    <section id="collaboration" className="relative rounded-xl border border-border bg-card p-6 shadow-md">
      <p className="font-serif text-6xl leading-none text-muted" aria-hidden>
        “
      </p>
      <h2 className="mt-2 text-sm font-semibold tracking-wide text-foreground uppercase">
        Collaboration (A2UI)
      </h2>
      <p className="mt-1 text-xs text-muted-foreground">
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
          <div className="rounded-lg border border-border bg-card p-4">
            <p className="text-xl font-semibold text-foreground">
              Extraction confirm — {widget.recommended.unit} vs {widget.alternate.unit}
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              Two readings disagree. Confirming recalculates the line and stores policy for this
              company.
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
                className="glow-primary rounded-full bg-primary px-4 py-2.5 text-left text-sm font-semibold text-primary-foreground shadow-sm transition hover:opacity-90 disabled:opacity-60"
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
                className="rounded-full bg-accent px-4 py-2.5 text-left text-sm font-semibold text-accent-foreground transition hover:bg-accent/80 disabled:opacity-60"
              >
                Use {widget.alternate.quantity.toLocaleString()} {widget.alternate.unit} →{" "}
                {widget.alternate_tco2e.toFixed(3)} tCO₂e
              </button>
            </div>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">No material gap. The agent is not asking.</p>
        )}
      </div>
    </section>
  );
}
