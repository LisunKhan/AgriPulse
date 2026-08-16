import type { AlertRecord, HealthResponse, TelemetryRecord } from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ||
  "http://localhost:8000";

export const WS_URL =
  process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws/telemetry";

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`API ${path} failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function fetchHealth() {
  return getJson<HealthResponse>("/health");
}

export function fetchLatestTelemetry() {
  return getJson<TelemetryRecord[]>("/telemetry/latest");
}

export function fetchTelemetryHistory(limit = 80) {
  return getJson<TelemetryRecord[]>(`/telemetry?limit=${limit}`);
}

export function fetchOpenAlerts(limit = 20) {
  return getJson<AlertRecord[]>(`/alerts?acknowledged=false&limit=${limit}`);
}

export async function acknowledgeAlert(publicId: string): Promise<AlertRecord> {
  const res = await fetch(`${API_BASE}/alerts/${publicId}/ack`, {
    method: "POST",
  });
  if (!res.ok) {
    throw new Error(`Failed to acknowledge alert: ${res.status}`);
  }
  return res.json() as Promise<AlertRecord>;
}
