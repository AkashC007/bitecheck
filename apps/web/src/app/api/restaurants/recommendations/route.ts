import "server-only";

import { getApiBaseUrl } from "@/lib/api/server-config";

const BACKEND_TIMEOUT_MS = 5_000;

export async function POST(request: Request): Promise<Response> {
  const baseUrl = getApiBaseUrl();
  const backendUrl = new URL(
    "/restaurants/recommendations",
    `${baseUrl.replace(/\/$/, "")}/`,
  );

  try {
    const requestBody = await request.text();
    const response = await fetch(backendUrl, {
      method: "POST",
      cache: "no-store",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: requestBody,
      signal: AbortSignal.timeout(BACKEND_TIMEOUT_MS),
    });
    const body = await response.text();
    return new Response(body, {
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
          "The recommendation service is temporarily unavailable. Please try again.",
      },
      { status: 503 },
    );
  }
}
