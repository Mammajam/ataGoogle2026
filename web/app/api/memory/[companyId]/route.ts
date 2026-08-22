import { NextRequest } from "next/server";
import { proxyJson } from "@/lib/proxy";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ companyId: string }> },
) {
  const { companyId } = await params;
  return proxyJson(req, `/api/memory/${companyId}`);
}
