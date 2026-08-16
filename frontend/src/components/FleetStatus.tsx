"use client";

import { formatFixed } from "@/lib/format";
import type { TelemetryRecord } from "@/lib/types";

function statusTone(status: string) {
  if (status === "spoilage_risk") return "text-risk";
  if (status === "warning") return "text-warn";
  return "text-chill";
}

type Props = {
  latest: TelemetryRecord[];
};

export function FleetStatus({ latest }: Props) {
  return (
    <section className="animate-rise" style={{ animationDelay: "80ms" }}>
      <div className="mb-4 flex items-end justify-between gap-3">
        <h2 className="font-display text-2xl tracking-tight text-ink">Fleet status</h2>
        <p className="font-sans text-sm text-ink/60">Live cold-chain readings</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {latest.map((truck) => (
          <article
            key={truck.device_id}
            className="border-t-2 border-field/70 pt-3"
          >
            <div className="flex items-start justify-between gap-2">
              <h3 className="font-sans text-lg font-semibold text-ink">
                {truck.device_id}
              </h3>
              <span
                className={`font-sans text-xs font-semibold uppercase tracking-[0.14em] ${statusTone(truck.status)} ${
                  truck.status === "spoilage_risk" ? "animate-pulse-soft" : ""
                }`}
              >
                {truck.status.replaceAll("_", " ")}
              </span>
            </div>
            <dl className="mt-3 grid grid-cols-2 gap-x-3 gap-y-2 font-sans text-sm">
              <div>
                <dt className="text-ink/50">Temp</dt>
                <dd className="text-base font-medium text-ink">
                  {formatFixed(truck.temperature_c, 1)}°C
                </dd>
              </div>
              <div>
                <dt className="text-ink/50">Humidity</dt>
                <dd className="text-base font-medium text-ink">
                  {formatFixed(truck.humidity_pct, 1)}%
                </dd>
              </div>
              <div className="col-span-2">
                <dt className="text-ink/50">Position</dt>
                <dd className="text-ink/80">
                  {formatFixed(truck.lat, 4)}, {formatFixed(truck.lng, 4)}
                </dd>
              </div>
            </dl>
          </article>
        ))}
        {latest.length === 0 && (
          <p className="font-sans text-sm text-ink/60">Waiting for telemetry…</p>
        )}
      </div>
    </section>
  );
}
