export type TelemetryRecord = {
  public_id: string;
  device_id: string;
  temperature_c: number;
  humidity_pct: number;
  lat: number;
  lng: number;
  status: "ok" | "warning" | "spoilage_risk" | string;
  recorded_at: string;
  cargo?: string | null;
};

export type AlertRecord = {
  public_id: string;
  device_id: string;
  alert_type: string;
  message: string;
  temperature_c?: number | null;
  humidity_pct?: number | null;
  created_at: string;
  acknowledged: boolean;
};

export type HealthResponse = {
  status: string;
  database: string;
  mqtt: string;
  app: string;
};

export type WsEnvelope =
  | { event: "telemetry"; data: TelemetryRecord }
  | { event: "alert"; data: AlertRecord };
