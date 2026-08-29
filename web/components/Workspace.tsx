"use client";

import { useEffect, useMemo, useState } from "react";
import { confirmExtraction, getAgentHealth, getMemory, runAudit } from "@/lib/agent-client";
import type { AuditEvent, CompanyProfile, ConfirmPayload, Draft } from "@/lib/types";
import { A2uiSurface } from "./A2uiSurface";
import { Dropzone } from "./Dropzone";
import { InventoryTable } from "./InventoryTable";
import { MemoryChip } from "./MemoryChip";

const PROFILE_KEY = "greenchain.company.v1";

const DEFAULT_PROFILE: CompanyProfile = {
  company_id: "",
  company_name: "",
  reporting_year: new Date().getFullYear(),
  region: "UK",
};

const FEATURES = [
  {
    title: "Autonomous draft",
    body: "Any conforming CSV, bill, and receipt become an inventory before anyone types.",
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
    body: "A2UI appears only when two readings would move company tCO₂e by more than 5%.",
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
    body: "Confirm once. The next close for this company applies the unit policy silently.",
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

function loadProfile(): CompanyProfile {
  try {
    const raw = localStorage.getItem(PROFILE_KEY);
    if (!raw) return DEFAULT_PROFILE;
    return { ...DEFAULT_PROFILE, ...JSON.parse(raw) };
  } catch {
    return DEFAULT_PROFILE;
  }
}

export function Workspace() {
  const [files, setFiles] = useState<File[]>([]);
  const [profile, setProfile] = useState<CompanyProfile>(DEFAULT_PROFILE);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [logEvents, setLogEvents] = useState<AuditEvent[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [memoryKeys, setMemoryKeys] = useState<string[]>([]);
  const [erpLive, setErpLive] = useState(false);

  useEffect(() => {
    setProfile(loadProfile());
  }, []);

  useEffect(() => {
    getAgentHealth()
      .then((health) => setErpLive(Boolean(health.erp_live)))
      .catch(() => setErpLive(false));
  }, []);

  useEffect(() => {
    localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
  }, [profile]);

  useEffect(() => {
    const id = profile.company_id.trim();
    if (!id) {
      setMemoryKeys([]);
      return;
    }
    getMemory(id)
      .then((mem) => {
        const keys = (mem.overrides || [])
          .map((item) => String(item.key || ""))
          .filter(Boolean);
        setMemoryKeys(keys);
      })
      .catch(() => undefined);
  }, [profile.company_id]);

  const canRun = Boolean(profile.company_id.trim()) && (files.length > 0 || erpLive) && !busy;

  const chipVisible =
    Boolean(draft?.policy_applied) || (memoryKeys.length > 0 && draft?.widget == null && Boolean(draft));
  const chipKeys = draft?.policy_keys?.length ? draft.policy_keys : memoryKeys;

  const events = useMemo(
    () => (logEvents.length > 0 ? logEvents : draft?.events || []),
    [draft, logEvents],
  );

  async function onRun() {
    if (!canRun) return;
    setBusy(true);
    setError(null);
    setLogEvents([]);
    try {
      const next = await runAudit(files, profile, (event) => {
        setLogEvents((prev) => [...prev, event]);
      }, erpLive);
      setDraft(next);
      setLogEvents(next.events?.length ? next.events : []);
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
      const next = await confirmExtraction({
        ...payload,
        company_id: profile.company_id.trim(),
      });
      setDraft(next);
      setMemoryKeys(next.policy_keys || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Confirm failed");
    } finally {
      setBusy(false);
    }
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
            disabled={!canRun}
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
              Drafts a GHG inventory from this company’s mixed evidence, then collaborates only where a
              human decision is required — and remembers how this company audits.
            </p>
            <div className="mt-6 grid grid-cols-2 gap-3">
              <label className="col-span-2 text-xs text-muted-foreground">
                Company id
                <input
                  className="mt-1 w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground"
                  value={profile.company_id}
                  onChange={(event) => setProfile((prev) => ({ ...prev, company_id: event.target.value }))}
                  placeholder="acme-logistics"
                />
              </label>
              <label className="col-span-2 text-xs text-muted-foreground">
                Display name
                <input
                  className="mt-1 w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground"
                  value={profile.company_name}
                  onChange={(event) => setProfile((prev) => ({ ...prev, company_name: event.target.value }))}
                  placeholder="Acme Logistics Ltd"
                />
              </label>
              <label className="text-xs text-muted-foreground">
                Reporting year
                <input
                  type="number"
                  className="mt-1 w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground"
                  value={profile.reporting_year}
                  onChange={(event) =>
                    setProfile((prev) => ({ ...prev, reporting_year: Number(event.target.value) }))
                  }
                />
              </label>
              <label className="text-xs text-muted-foreground">
                Region / grid
                <input
                  className="mt-1 w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground"
                  value={profile.region}
                  onChange={(event) => setProfile((prev) => ({ ...prev, region: event.target.value }))}
                  placeholder="UK"
                />
              </label>
            </div>
            <div className="mt-8 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={onRun}
                disabled={!canRun}
                className="inline-flex items-center gap-2 rounded-full bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground shadow-md transition hover:opacity-90 disabled:opacity-60"
              >
                {busy ? "Running close…" : "Run audit"}
                <ArrowIcon />
              </button>
            </div>
          </div>
          <Dropzone files={files} onFiles={setFiles} erpLive={erpLive} />
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
          <InventoryTable draft={draft} busy={busy} />
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
            <p>Events stream here while Run audit is in flight.</p>
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
