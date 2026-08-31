const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const DEFAULT_HEALTH_TIMEOUT_MS = 2_000;
const MAX_HEALTH_TIMEOUT_MS = 60_000;

type ServerEnvironment = Record<string, string | undefined>;

export function getApiBaseUrl(
  environment: ServerEnvironment = process.env,
): string {
  const publicUrl = environment.API_BASE_URL?.trim();

  if (publicUrl) {
    return publicUrl;
  }

  const privateHost = environment.API_BASE_HOSTPORT?.trim();

  if (privateHost) {
    return `http://${privateHost}`;
  }

  return DEFAULT_API_BASE_URL;
}

export function getApiHealthTimeoutMs(
  environment: ServerEnvironment = process.env,
): number {
  const configuredTimeout = Number(environment.API_HEALTH_TIMEOUT_MS);

  if (
    Number.isInteger(configuredTimeout) &&
    configuredTimeout >= DEFAULT_HEALTH_TIMEOUT_MS &&
    configuredTimeout <= MAX_HEALTH_TIMEOUT_MS
  ) {
    return configuredTimeout;
  }

  return DEFAULT_HEALTH_TIMEOUT_MS;
}
