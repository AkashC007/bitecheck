type BackendHealthPayload = {
  status: "ok";
  service: string;
};

export type BackendHealthResult =
  | {
      state: "connected";
      service: string;
    }
  | {
      state: "unavailable";
    };

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const HEALTH_TIMEOUT_MS = 2_000;

function isBackendHealthPayload(value: unknown): value is BackendHealthPayload {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const payload = value as Record<string, unknown>;

  return payload.status === "ok" && typeof payload.service === "string";
}

export async function getBackendHealth(): Promise<BackendHealthResult> {
  const baseUrl = process.env.API_BASE_URL ?? DEFAULT_API_BASE_URL;
  const healthUrl = `${baseUrl.replace(/\/$/, "")}/health`;

  try {
    const response = await fetch(healthUrl, {
      cache: "no-store",
      headers: {
        Accept: "application/json",
      },
      signal: AbortSignal.timeout(HEALTH_TIMEOUT_MS),
    });

    if (!response.ok) {
      return { state: "unavailable" };
    }

    const payload: unknown = await response.json();

    if (!isBackendHealthPayload(payload)) {
      return { state: "unavailable" };
    }

    return {
      state: "connected",
      service: payload.service,
    };
  } catch {
    return { state: "unavailable" };
  }
}
