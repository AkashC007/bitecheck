import "server-only";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

export async function POST(request: Request): Promise<Response> {
  const baseUrl = process.env.API_BASE_URL ?? DEFAULT_API_BASE_URL;
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
