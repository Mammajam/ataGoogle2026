import { NextRequest } from "next/server";
import { agentBase } from "@/lib/proxy";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(
  _req: NextRequest,
  context: { params: Promise<{ runId: string; name: string }> },
) {
  const { runId, name } = await context.params;
  const res = await fetch(
    `${agentBase()}/api/audit/${encodeURIComponent(runId)}/artifacts/${encodeURIComponent(name)}`,
    { cache: "no-store" },
  );
  return new Response(res.body, {
    status: res.status,
    headers: {
      "Content-Type": res.headers.get("Content-Type") || "application/octet-stream",
      "Cache-Control": "private, max-age=60",
    },
  });
}
