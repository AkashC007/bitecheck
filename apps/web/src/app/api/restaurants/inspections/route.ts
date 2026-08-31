import "server-only";

import { getApiBaseUrl } from "@/lib/api/server-config";

const BACKEND_TIMEOUT_MS = 12_000;

export async function POST(request: Request): Promise<Response> {
  const baseUrl = getApiBaseUrl();
  const backendUrl = new URL(
    "/restaurants/inspections/explore",
    `${baseUrl.replace(/\/$/, "")}/`,
  );

  try {
    const response = await fetch(backendUrl, {
      method: "POST",
      cache: "no-store",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: await request.text(),
      signal: AbortSignal.timeout(BACKEND_TIMEOUT_MS),
    });
    return new Response(await response.text(), {
      status: response.status,
      headers: {
        "content-type":
          response.headers.get("content-type") ?? "application/json",
      },
    });
  } catch {
    return Response.json(
      {
        detail:
          "The live City inspection service is temporarily unavailable. Please try again.",
      },
      { status: 503 },
    );
  }
}
