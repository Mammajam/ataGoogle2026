"use client";

import { useEffect, useMemo, useState } from "react";
import { confirmExtraction, getMemory, runAudit } from "@/lib/agent-client";
import type { ConfirmPayload, Draft } from "@/lib/types";
import { A2uiSurface } from "./A2uiSurface";
import { Dropzone } from "./Dropzone";
import { InventoryTable } from "./InventoryTable";
import { MemoryChip } from "./MemoryChip";

const COMPANY = "northwind-energy";

export function Workspace() {
  const [files, setFiles] = useState<File[]>([]);
  const [usingDemoPack, setUsingDemoPack] = useState(true);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [memoryKeys, setMemoryKeys] = useState<string[]>([]);

  useEffect(() => {
    getMemory(COMPANY)
      .then((mem) => {
        const keys = (mem.overrides || [])
          .map((item) => String(item.key || ""))
          .filter(Boolean);
        setMemoryKeys(keys);
      })
      .catch(() => undefined);
  }, []);

  const chipVisible = Boolean(draft?.policy_applied) || (memoryKeys.length > 0 && draft?.widget == null && Boolean(draft));
  const chipKeys = draft?.policy_keys?.length ? draft.policy_keys : memoryKeys;

  const events = useMemo(() => draft?.events || [], [draft]);

  async function onRun() {
    setBusy(true);
    setError(null);
    try {
      const next = await runAudit(usingDemoPack ? [] : files, COMPANY);
      setDraft(next);
      if (next.policy_applied) setMemoryKeys(next.policy_keys || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Audit failed");
    } finally {
      setBusy(false);
    }
  }

  async function onConfirm(payload: ConfirmPayload) {
    setBusy(true);
    setError(null);
    try {
      const next = await confirmExtraction({ ...payload, company_id: COMPANY });
      setDraft(next);
      setMemoryKeys(next.policy_keys || ["electricity_unit"]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Confirm failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto max-w-6xl px-4 py-8">
      <header className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="sans text-xs font-semibold uppercase tracking-[0.2em] text-[#c4a35a]">
            The Collaborative Partner
          </p>
          <h1 className="mt-1 text-4xl text-[#1b4d3e]">GreenChain</h1>
          <p className="mt-2 max-w-xl text-[#3d4a42]">
            Drafts a GHG inventory from mixed evidence on its own, then collaborates
            only where a human decision is required — and remembers how this company audits.
          </p>
        </div>
        <div className="flex flex-col items-end gap-2">
          <MemoryChip visible={chipVisible} keys={chipKeys} />
          <button
            type="button"
            onClick={onRun}
            disabled={busy}
            className="sans rounded-full bg-[#c4a35a] px-6 py-3 text-sm font-bold tracking-wide text-[#14251c] shadow hover:bg-[#d4b56a] disabled:opacity-60"
          >
            {busy ? "Running close…" : "Run audit"}
          </button>
        </div>
      </header>

      <Dropzone
        files={files}
        onFiles={(next) => {
          setFiles(next);
          setUsingDemoPack(next.length === 0);
        }}
        usingDemoPack={usingDemoPack}
        onUseDemoPack={() => {
          setFiles([]);
          setUsingDemoPack(true);
        }}
      />

      {error ? (
        <p className="sans mt-4 rounded-lg bg-[#f4d4cc] px-3 py-2 text-sm text-[#9b2c2c]">{error}</p>
      ) : null}

      <div className="mt-5 grid gap-5 lg:grid-cols-[minmax(0,1.4fr)_minmax(280px,0.8fr)]">
        <InventoryTable draft={draft} />
        <A2uiSurface
          messages={draft?.a2ui || []}
          widget={draft?.widget || null}
          busy={busy}
          onConfirm={onConfirm}
        />
      </div>

      <section className="sans mt-5 rounded-2xl border border-[#d9d0bf] bg-[#fbf8f1] p-4 text-xs text-[#5c6b62]">
        <div className="mb-2 font-semibold uppercase tracking-wide text-[#1b4d3e]">Job log</div>
        {events.length === 0 ? (
          <p>No questions before the draft. Events stream here after Run audit.</p>
        ) : (
          <ol className="space-y-1">
            {events.map((event, index) => (
              <li key={`${event.step}-${index}`}>
                <span className="font-semibold text-[#1b4d3e]">{event.step}</span> — {event.message}
              </li>
            ))}
          </ol>
        )}
      </section>
    </main>
  );
}
