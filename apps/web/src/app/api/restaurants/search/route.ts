import "server-only";

import { getApiBaseUrl } from "@/lib/api/server-config";

const BACKEND_TIMEOUT_MS = 5_000;

export async function GET(request: Request): Promise<Response> {
  const requestUrl = new URL(request.url);
  const baseUrl = getApiBaseUrl();
  const backendUrl = new URL(
    "/restaurants/search",
    `${baseUrl.replace(/\/$/, "")}/`,
  );
  backendUrl.search = requestUrl.search;

  try {
    const response = await fetch(backendUrl, {
      cache: "no-store",
      headers: { Accept: "application/json" },
      signal: AbortSignal.timeout(BACKEND_TIMEOUT_MS),
    });
    const body = await response.text();

    return new Response(body, {
      status: response.status,
      headers: {
        "content-type": response.headers.get("content-type") ??
          "application/json",
      },
    });
  } catch {
    return Response.json(
      {
        detail:
          "The restaurant service is temporarily unavailable. Please try again.",
      },
      { status: 503 },
    );
  }
}
