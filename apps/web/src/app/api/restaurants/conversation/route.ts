import "server-only";

import { getApiBaseUrl } from "@/lib/api/server-config";

export async function POST(request: Request): Promise<Response> {
  const baseUrl = getApiBaseUrl();
  const backendUrl = new URL(
    "/restaurants/conversation",
    `${baseUrl.replace(/\/$/, "")}/`,
  );
  try {
    const response = await fetch(backendUrl, {
      method: "POST",
      cache: "no-store",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: await request.text(),
      signal: AbortSignal.timeout(5_000),
    });
    return new Response(await response.text(), {
      status: response.status,
      headers: {
        "content-type": response.headers.get("content-type") ?? "application/json",
      },
    });
  } catch {
    return Response.json(
      { detail: "The conversation service is temporarily unavailable." },
      { status: 503 },
    );
  }
}
