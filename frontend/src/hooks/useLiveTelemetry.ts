"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import {
  acknowledgeAlert,
  fetchHealth,
  fetchLatestTelemetry,
  fetchOpenAlerts,
  fetchTelemetryHistory,
  WS_URL,
} from "@/lib/api";
import type { AlertRecord, HealthResponse, TelemetryRecord, WsEnvelope } from "@/lib/types";

function upsertLatest(
  current: TelemetryRecord[],
  incoming: TelemetryRecord,
): TelemetryRecord[] {
  const without = current.filter((row) => row.device_id !== incoming.device_id);
  return [...without, incoming].sort((a, b) => a.device_id.localeCompare(b.device_id));
}

export function useLiveTelemetry() {
  const [latest, setLatest] = useState<TelemetryRecord[]>([]);
  const [history, setHistory] = useState<TelemetryRecord[]>([]);
  const [alerts, setAlerts] = useState<AlertRecord[]>([]);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const bootstrap = useCallback(async () => {
    try {
      setLoading(true);
      const [latestRows, historyRows, alertRows, healthRow] = await Promise.all([
        fetchLatestTelemetry(),
        fetchTelemetryHistory(90),
        fetchOpenAlerts(),
        fetchHealth(),
      ]);
      setLatest(latestRows);
      setHistory(historyRows);
      setAlerts(alertRows);
      setHealth(healthRow);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void bootstrap();
  }, [bootstrap]);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let closed = false;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;

    const connect = () => {
      ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        if (!closed) setConnected(true);
      };

      ws.onclose = () => {
        if (closed) return;
        setConnected(false);
        retryTimer = setTimeout(connect, 2500);
      };

      ws.onerror = () => {
        ws?.close();
      };

      ws.onmessage = (event) => {
        try {
          const envelope = JSON.parse(event.data) as WsEnvelope;
          if (envelope.event === "telemetry") {
            setLatest((prev) => upsertLatest(prev, envelope.data));
            setHistory((prev) => [envelope.data, ...prev].slice(0, 120));
          } else if (envelope.event === "alert") {
            setAlerts((prev) => {
              if (prev.some((a) => a.public_id === envelope.data.public_id)) {
                return prev;
              }
              return [envelope.data, ...prev].slice(0, 30);
            });
          }
        } catch {
          // ignore malformed frames
        }
      };
    };

    connect();

    return () => {
      closed = true;
      if (retryTimer) clearTimeout(retryTimer);
      ws?.close();
    };
  }, []);

  const ackAlert = useCallback(async (publicId: string) => {
    const updated = await acknowledgeAlert(publicId);
    setAlerts((prev) => prev.filter((a) => a.public_id !== updated.public_id));
  }, []);

  const riskCount = useMemo(
    () => latest.filter((row) => row.status === "spoilage_risk").length,
    [latest],
  );

  return {
    latest,
    history,
    alerts,
    health,
    connected,
    error,
    loading,
    riskCount,
    ackAlert,
    refresh: bootstrap,
  };
}
