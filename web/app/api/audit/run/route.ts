import { NextRequest } from "next/server";
import { agentBase } from "@/lib/proxy";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(req: NextRequest) {
  const incoming = await req.formData();
  const outbound = new FormData();
  outbound.append("company_id", String(incoming.get("company_id") || "northwind-energy"));
  for (const [key, value] of incoming.entries()) {
    if (key === "files" && value instanceof File) {
      outbound.append("files", value, value.name);
    }
  }
  const res = await fetch(`${agentBase()}/api/audit/run`, {
    method: "POST",
    body: outbound,
    cache: "no-store",
  });
  const text = await res.text();
  return new Response(text, {
    status: res.status,
    headers: { "Content-Type": res.headers.get("Content-Type") || "application/json" },
  });
}
