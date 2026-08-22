"use client";

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
      <section className="rounded-2xl border border-[#d9d0bf] bg-[#fbf8f1] p-5 shadow-sm">
        <h2 className="sans text-sm font-semibold tracking-wide text-[#1b4d3e] uppercase">
          GHG draft inventory
        </h2>
        <p className="mt-6 text-[#5c6b62]">
          Click <strong>Run audit</strong>. The draft appears before you answer anything.
        </p>
      </section>
    );
  }

  return (
    <section className="rounded-2xl border border-[#d9d0bf] bg-[#fbf8f1] p-5 shadow-sm">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="sans text-sm font-semibold tracking-wide text-[#1b4d3e] uppercase">
            GHG draft inventory
          </h2>
          <p className="text-sm text-[#5c6b62]">
            {draft.company_name} · {draft.reporting_year} · {draft.status}
          </p>
        </div>
        <div className="sans text-right">
          <div className="text-3xl font-semibold text-[#1b4d3e]">{fmt(draft.totals.total_tco2e)}</div>
          <div className="text-xs uppercase tracking-wide text-[#5c6b62]">tCO₂e total</div>
        </div>
      </div>
      <div className="sans mb-4 grid grid-cols-3 gap-2 text-center text-xs">
        <div className="rounded-lg bg-white/80 p-2">
          S1 {fmt(draft.totals.scope1_tco2e)}
        </div>
        <div className="rounded-lg bg-white/80 p-2">
          S2 {fmt(draft.totals.scope2_tco2e)}
        </div>
        <div className="rounded-lg bg-white/80 p-2">
          S3 {fmt(draft.totals.scope3_tco2e)}
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="sans w-full min-w-[720px] border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-[#d9d0bf] text-xs uppercase tracking-wide text-[#5c6b62]">
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
            {draft.lines.map((line) => (
              <tr
                key={line.id}
                className={`border-b border-[#efe8d8] ${
                  line.gap_flag === "unit_conflict" ? "bg-[#f4d4cc]/70" : ""
                }`}
              >
                <td className="py-2 pr-2">
                  {line.source_thumb.endsWith(".pdf") ? (
                    <span className="inline-flex h-8 w-8 items-center justify-center rounded bg-[#1b4d3e] text-[10px] text-white">
                      PDF
                    </span>
                  ) : (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={thumbSrc(line.source_thumb)}
                      alt={line.source}
                      className="h-8 w-8 rounded object-cover"
                    />
                  )}
                </td>
                <td className="py-2 pr-2">
                  {line.scope}
                  {line.category ? ` / C${line.category}` : ""}
                </td>
                <td className="py-2 pr-2 font-medium">{line.activity}</td>
                <td className="py-2 pr-2">
                  {fmt(line.quantity)} {line.unit}
                </td>
                <td className="py-2 pr-2 font-semibold">{fmt(line.tco2e)}</td>
                <td className="py-2 pr-2">{line.method}</td>
                <td className="py-2 pr-2">{Math.round(line.confidence * 100)}%</td>
                <td className="py-2">
                  {line.gap_flag === "unit_conflict" ? (
                    <span className="rounded bg-[#9b2c2c] px-2 py-0.5 text-xs text-white">
                      material
                    </span>
                  ) : line.assumption ? (
                    <span className="rounded bg-[#e8dcc3] px-2 py-0.5 text-xs">assumed</span>
                  ) : (
                    <span className="text-[#5c6b62]">—</span>
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
