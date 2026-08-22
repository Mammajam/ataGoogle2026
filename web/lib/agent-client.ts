import type { ConfirmPayload, Draft, MemoryResponse } from "./types";

async function readJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed (${res.status})`);
  }
  return (await res.json()) as T;
}

export async function runAudit(files: File[], companyId = "northwind-energy"): Promise<Draft> {
  const body = new FormData();
  body.append("company_id", companyId);
  for (const file of files) {
    body.append("files", file);
  }
  const res = await fetch("/api/audit/run", { method: "POST", body });
  return readJson<Draft>(res);
}

export async function confirmExtraction(payload: ConfirmPayload): Promise<Draft> {
  const res = await fetch("/api/audit/confirm", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return readJson<Draft>(res);
}

export async function getMemory(companyId = "northwind-energy"): Promise<MemoryResponse> {
  const res = await fetch(`/api/memory/${companyId}`, { cache: "no-store" });
  return readJson<MemoryResponse>(res);
}
