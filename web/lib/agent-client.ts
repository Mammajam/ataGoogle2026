import type { AgentHealth, CompanyProfile, ConfirmPayload, Draft, MemoryResponse } from "./types";

async function readJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed (${res.status})`);
  }
  return (await res.json()) as T;
}

function parseSseBlock(block: string): { event: string; data: Record<string, unknown> } | null {
  const lines = block.split("\n");
  let event = "message";
  const dataLines: string[] = [];
  for (const line of lines) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
  }
  if (dataLines.length === 0) return null;
  try {
    return { event, data: JSON.parse(dataLines.join("\n")) as Record<string, unknown> };
  } catch {
    return null;
  }
}

export async function runAudit(
  files: File[],
  profile: CompanyProfile,
  onEvent?: (event: { step: string; message: string }) => void,
  allowEmptyFiles = false,
): Promise<Draft> {
  if (!profile.company_id.trim()) {
    throw new Error("company_id is required");
  }
  if (!files.length && !allowEmptyFiles) {
    throw new Error("at least one evidence file is required");
  }
  const body = new FormData();
  body.append("company_id", profile.company_id.trim());
  if (profile.company_name) body.append("company_name", profile.company_name);
  body.append("reporting_year", String(profile.reporting_year));
  if (profile.region) body.append("region", profile.region);
  for (const file of files) {
    body.append("files", file);
  }
  const res = await fetch("/api/audit/run", {
    method: "POST",
    body,
    headers: { Accept: "text/event-stream" },
  });
  const contentType = res.headers.get("content-type") || "";
  if (!contentType.includes("text/event-stream")) {
    return readJson<Draft>(res);
  }
  if (!res.body) {
    throw new Error("No stream body");
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let draft: Draft | null = null;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() || "";
    for (const chunk of chunks) {
      const parsed = parseSseBlock(chunk);
      if (!parsed) continue;
      const step = String(parsed.data.step || parsed.event);
      const message = String(parsed.data.message || "");
      if (step && message) onEvent?.({ step, message });
      if (parsed.data.draft && typeof parsed.data.draft === "object") {
        draft = parsed.data.draft as Draft;
      }
    }
  }
  if (!draft) {
    throw new Error("Stream ended without a draft");
  }
  return draft;
}

export async function confirmExtraction(payload: ConfirmPayload): Promise<Draft> {
  const res = await fetch("/api/audit/confirm", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return readJson<Draft>(res);
}

export async function getMemory(companyId: string): Promise<MemoryResponse> {
  const res = await fetch(`/api/memory/${encodeURIComponent(companyId)}`, { cache: "no-store" });
  return readJson<MemoryResponse>(res);
}

export async function getAgentHealth(): Promise<AgentHealth> {
  const res = await fetch("/api/health", { cache: "no-store" });
  return readJson<AgentHealth>(res);
}
