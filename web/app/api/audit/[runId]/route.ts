import { NextRequest } from "next/server";
import { proxyJson } from "@/lib/proxy";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(req: NextRequest, { params }: { params: Promise<{ runId: string }> }) {
  const { runId } = await params;
  return proxyJson(req, `/api/audit/${runId}`);
}
