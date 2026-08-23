"use client";

import Image from "next/image";
import type { Draft } from "@/lib/types";

function fmt(n: number) {
  return n.toLocaleString(undefined, { maximumFractionDigits: 3 });
}

function thumbSrc(name: string) {
  return `/fixtures/${name}`;
}

export function InventoryTable({ draft }: { draft: Draft | null }) {
  if (!draft) {
    return (
      <section id="inventory" className="rounded-xl bg-card p-6 shadow-md">
        <h2 className="text-sm font-semibold tracking-wide text-foreground uppercase">
          GHG draft inventory
        </h2>
        <p className="mt-6 text-muted-foreground">
          Click <strong className="text-foreground">Run audit</strong>. The draft appears before you
          answer anything.
        </p>
      </section>
    );
  }

  return (
    <section id="inventory" className="rounded-xl bg-card p-6 shadow-md">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold tracking-wide text-foreground uppercase">
            GHG draft inventory
          </h2>
          <p className="text-sm text-muted-foreground">
            {draft.company_name} · {draft.reporting_year} · {draft.status}
          </p>
        </div>
        <div className="text-right">
          <div className="font-mono text-3xl font-semibold text-primary">
            {fmt(draft.totals.total_tco2e)}
          </div>
          <div className="text-xs uppercase tracking-wide text-muted-foreground">tCO₂e total</div>
        </div>
      </div>
      <div className="mb-4 grid grid-cols-3 gap-2 text-center text-xs">
        <div className="rounded-sm bg-background p-2 text-chart-1">
          S1 <span className="font-mono font-semibold">{fmt(draft.totals.scope1_tco2e)}</span>
        </div>
        <div className="rounded-sm bg-background p-2 text-chart-2">
          S2 <span className="font-mono font-semibold">{fmt(draft.totals.scope2_tco2e)}</span>
        </div>
        <div className="rounded-sm bg-background p-2 text-chart-3">
          S3 <span className="font-mono font-semibold">{fmt(draft.totals.scope3_tco2e)}</span>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-180 border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-border text-xs uppercase tracking-wide text-muted-foreground">
              <th className="py-2 pr-2">Src</th>
              <th className="py-2 pr-2">Scope</th>
              <th className="py-2 pr-2">Activity</th>
              <th className="py-2 pr-2">Quantity</th>
              <th className="py-2 pr-2">tCO₂e</th>
              <th className="py-2 pr-2">Method</th>
              <th className="py-2 pr-2">Conf.</th>
              <th className="py-2">Gap</th>
            </tr>
          </thead>
          <tbody>
            {draft.lines.map((line, index) => (
              <tr
                key={line.id}
                className={`border-b border-border ${
                  line.gap_flag === "unit_conflict"
                    ? "bg-destructive/10"
                    : index % 2 === 1
                      ? "bg-muted/70"
                      : ""
                }`}
              >
                <td className="py-2 pr-2">
                  {line.source_thumb.endsWith(".pdf") ? (
                    <span className="inline-flex h-8 w-8 items-center justify-center rounded-sm bg-primary text-[10px] font-semibold text-primary-foreground">
                      PDF
                    </span>
                  ) : (
                    <Image
                      src={thumbSrc(line.source_thumb)}
                      alt={line.source}
                      width={32}
                      height={32}
                      className="broken-image-fallback h-8 w-8 rounded-sm object-cover"
                    />
                  )}
                </td>
                <td className="py-2 pr-2">
                  {line.scope}
                  {line.category ? ` / C${line.category}` : ""}
                </td>
                <td className="py-2 pr-2 font-medium">{line.activity}</td>
                <td className="py-2 pr-2 font-mono">
                  {fmt(line.quantity)} {line.unit}
                </td>
                <td className="py-2 pr-2 font-mono font-semibold">{fmt(line.tco2e)}</td>
                <td className="py-2 pr-2">{line.method}</td>
                <td className="py-2 pr-2 font-mono">{Math.round(line.confidence * 100)}%</td>
                <td className="py-2">
                  {line.gap_flag === "unit_conflict" ? (
                    <span className="rounded-full bg-destructive px-2 py-0.5 text-xs text-destructive-foreground">
                      material
                    </span>
                  ) : line.assumption ? (
                    <span className="rounded-full bg-accent px-2 py-0.5 text-xs text-accent-foreground">
                      assumed
                    </span>
                  ) : (
                    <span className="text-muted-foreground">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
