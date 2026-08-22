import { NextRequest } from "next/server";

export function agentBase(): string {
  return process.env.AGENT_URL || process.env.NEXT_PUBLIC_AGENT_URL || "http://localhost:8080";
}

export async function proxyJson(req: NextRequest, path: string, init?: RequestInit) {
  const res = await fetch(`${agentBase()}${path}`, {
    ...init,
    headers: {
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });
  const text = await res.text();
  return new Response(text, {
    status: res.status,
    headers: { "Content-Type": res.headers.get("Content-Type") || "application/json" },
  });
}
