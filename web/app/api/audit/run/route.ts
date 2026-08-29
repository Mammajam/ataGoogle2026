import { NextRequest } from "next/server";
import { agentBase } from "@/lib/proxy";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 300;

export async function POST(req: NextRequest) {
  const incoming = await req.formData();
  const outbound = new FormData();
  const companyId = String(incoming.get("company_id") || "").trim();
  if (!companyId) {
    return Response.json({ error: "company_id is required" }, { status: 400 });
  }
  outbound.append("company_id", companyId);
  for (const key of ["company_name", "reporting_year", "region"] as const) {
    const value = incoming.get(key);
    if (typeof value === "string" && value.trim()) {
      outbound.append(key, value.trim());
    }
  }
  for (const [key, value] of incoming.entries()) {
    if (key === "files" && value instanceof File) {
      outbound.append("files", value, value.name);
    }
  }
  const accept = req.headers.get("accept") || "application/json";
  const res = await fetch(`${agentBase()}/api/audit/run`, {
    method: "POST",
    body: outbound,
    cache: "no-store",
    headers: { Accept: accept },
  });
  return new Response(res.body, {
    status: res.status,
    headers: {
      "Content-Type": res.headers.get("Content-Type") || "application/json",
      "Cache-Control": "no-cache",
      "X-Accel-Buffering": "no",
    },
  });
}
