"use client";

import { useEffect, useMemo, useState } from "react";
import { confirmExtraction, getMemory, runAudit } from "@/lib/agent-client";
import type { ConfirmPayload, Draft } from "@/lib/types";
import { A2uiSurface } from "./A2uiSurface";
import { Dropzone } from "./Dropzone";
import { InventoryTable } from "./InventoryTable";
import { MemoryChip } from "./MemoryChip";

const COMPANY = "northwind-energy";

const FEATURES = [
  {
    title: "Autonomous draft",
    body: "ERP, bill, and receipt become a complete inventory before anyone types.",
    tone: "bg-primary/15 text-primary",
    icon: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M4 8h16M4 16h10" strokeLinecap="round" />
        <circle cx="18" cy="16" r="2.2" />
      </svg>
    ),
  },
  {
    title: "Material gate",
    body: "A2UI appears only for the planted kWh/MWh conflict — never as a chat first.",
    tone: "bg-accent text-accent-foreground",
    icon: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M12 4v2M12 18v2M6.2 6.2l1.4 1.4M16.4 16.4l1.4 1.4M4 12h2M18 12h2M6.2 17.8l1.4-1.4M16.4 7.6l1.4-1.4" strokeLinecap="round" />
        <circle cx="12" cy="12" r="3" />
      </svg>
    ),
  },
  {
    title: "Company memory",
    body: "Confirm once. The next close applies the unit policy silently.",
    tone: "bg-chart-3/20 text-chart-3",
    icon: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M12 12a3.5 3.5 0 1 0-3.5-3.5A3.5 3.5 0 0 0 12 12Zm0 0c-3.6 0-6.5 2-6.5 4.5V19h13v-2.5C18.5 14 15.6 12 12 12Z" strokeLinejoin="round" />
      </svg>
    ),
  },
] as const;

function ArrowIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M5 12h14M13 6l6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

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

  const chipVisible =
    Boolean(draft?.policy_applied) || (memoryKeys.length > 0 && draft?.widget == null && Boolean(draft));
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

  function onUseDemoPack() {
    setFiles([]);
    setUsingDemoPack(true);
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-5">
        <a href="#workspace" className="text-lg font-semibold text-foreground">
          GreenChain
        </a>
        <nav className="hidden items-center gap-8 text-sm text-muted-foreground md:flex">
          <a href="#workspace" className="transition hover:text-foreground">
            Workspace
          </a>
          <a href="#inventory" className="transition hover:text-foreground">
            Inventory
          </a>
          <a href="#collaboration" className="transition hover:text-foreground">
            Collaboration
          </a>
        </nav>
        <div className="flex items-center gap-3">
          <MemoryChip visible={chipVisible} keys={chipKeys} />
          <button
            type="button"
            onClick={onRun}
            disabled={busy}
            className="rounded-full bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground shadow-md transition hover:opacity-90 disabled:opacity-60"
          >
            {busy ? "Running close…" : "Run audit"}
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 pb-16">
        <section id="workspace" className="grid items-center gap-10 py-6 lg:grid-cols-2">
          <div>
            <p className="text-sm font-medium text-muted-foreground">The Collaborative Partner</p>
            <h1 className="mt-3 text-4xl font-bold tracking-tight lg:text-5xl">
              Close the period. <span className="text-primary">Ask only when it matters.</span>
            </h1>
            <p className="mt-4 max-w-xl text-lg text-muted-foreground">
              Drafts a GHG inventory from mixed evidence on its own, then collaborates only where a
              human decision is required — and remembers how this company audits.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={onRun}
                disabled={busy}
                className="inline-flex items-center gap-2 rounded-full bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground shadow-md transition hover:opacity-90 disabled:opacity-60"
              >
                {busy ? "Running close…" : "Run audit"}
                <ArrowIcon />
              </button>
              <button
                type="button"
                onClick={onUseDemoPack}
                className="rounded-full bg-accent px-6 py-3 text-sm font-semibold text-accent-foreground transition hover:bg-accent/80"
              >
                Use demo pack
              </button>
            </div>
          </div>
          <Dropzone
            files={files}
            onFiles={(next) => {
              setFiles(next);
              setUsingDemoPack(next.length === 0);
            }}
            usingDemoPack={usingDemoPack}
            onUseDemoPack={onUseDemoPack}
          />
        </section>

        <section className="grid gap-5 py-8 md:grid-cols-3">
          {FEATURES.map((feature) => (
            <article key={feature.title} className="rounded-xl bg-card p-6 shadow-md">
              <div className={`flex h-12 w-12 items-center justify-center rounded-full ${feature.tone}`}>
                {feature.icon}
              </div>
              <h2 className="mt-4 text-lg font-semibold text-card-foreground">{feature.title}</h2>
              <p className="mt-2 text-sm text-muted-foreground">{feature.body}</p>
            </article>
          ))}
        </section>

        {error ? (
          <p className="rounded-lg bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</p>
        ) : null}

        <div className="mt-2 grid gap-5 md:grid-cols-[minmax(0,1.35fr)_minmax(260px,0.85fr)]">
          <InventoryTable draft={draft} />
          <A2uiSurface
            messages={draft?.a2ui || []}
            widget={draft?.widget || null}
            busy={busy}
            onConfirm={onConfirm}
          />
        </div>

        <section className="mt-5 rounded-xl bg-card p-5 text-xs text-muted-foreground shadow-sm">
          <div className="mb-2 font-semibold uppercase tracking-wide text-foreground">Job log</div>
          {events.length === 0 ? (
            <p>No questions before the draft. Events stream here after Run audit.</p>
          ) : (
            <ol className="space-y-1 font-mono">
              {events.map((event, index) => (
                <li key={`${event.step}-${index}`}>
                  <span className="font-semibold text-foreground">{event.step}</span> — {event.message}
                </li>
              ))}
            </ol>
          )}
        </section>
      </main>

      <footer className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-8 text-sm text-muted-foreground">
        <p>
          <span className="font-semibold text-foreground">GreenChain</span>
          <span className="ml-2">© 2026 · All Things Agentic</span>
        </p>
        <nav className="flex flex-wrap gap-4">
          <a href="#workspace" className="hover:text-foreground">
            Workspace
          </a>
          <a href="#inventory" className="hover:text-foreground">
            Inventory
          </a>
          <a href="#collaboration" className="hover:text-foreground">
            Collaboration
          </a>
        </nav>
      </footer>
    </div>
  );
}
