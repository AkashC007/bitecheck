import assert from "node:assert/strict";
import test from "node:test";

import {
  getApiBaseUrl,
  getApiHealthTimeoutMs,
} from "../src/lib/api/server-config.js";

test("server config prefers an explicit public API URL", () => {
  assert.equal(
    getApiBaseUrl({
      API_BASE_URL: "https://api.example.com",
      API_BASE_HOSTPORT: "bitecheck-api:10000",
    }),
    "https://api.example.com",
  );
});

test("server config builds a private Render URL from host and port", () => {
  assert.equal(
    getApiBaseUrl({ API_BASE_HOSTPORT: "bitecheck-api:10000" }),
    "http://bitecheck-api:10000",
  );
});

test("server config keeps safe local and timeout defaults", () => {
  assert.equal(getApiBaseUrl({}), "http://127.0.0.1:8000");
  assert.equal(getApiHealthTimeoutMs({}), 2_000);
  assert.equal(getApiHealthTimeoutMs({ API_HEALTH_TIMEOUT_MS: "60000" }), 60_000);
  assert.equal(getApiHealthTimeoutMs({ API_HEALTH_TIMEOUT_MS: "invalid" }), 2_000);
});
