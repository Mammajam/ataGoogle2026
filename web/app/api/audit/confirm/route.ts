import { NextRequest } from "next/server";
import { proxyJson } from "@/lib/proxy";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(req: NextRequest) {
  const body = await req.text();
  return proxyJson(req, "/api/audit/confirm", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
  });
}
