"use client";

import { AlertBanner } from "@/components/AlertBanner";
import { FleetStatus } from "@/components/FleetStatus";
import { RouteMap } from "@/components/RouteMap";
import { TemperatureChart } from "@/components/TemperatureChart";
import { useLiveTelemetry } from "@/hooks/useLiveTelemetry";

export function Dashboard() {
  const {
    latest,
    history,
    alerts,
    health,
    connected,
    error,
    loading,
    riskCount,
    ackAlert,
  } = useLiveTelemetry();

  return (
    <main className="grid-atmosphere min-h-screen">
      <div className="mx-auto max-w-6xl px-5 pb-16 pt-8 sm:px-8">
        <header className="animate-rise mb-8 border-b border-line pb-8">
          <p className="font-sans text-xs font-semibold uppercase tracking-[0.22em] text-field">
            Cold-chain operations
          </p>
          <h1 className="mt-2 font-display text-5xl leading-none tracking-tight text-ink sm:text-6xl">
            AgriPulse
          </h1>
          <p className="mt-4 max-w-2xl font-sans text-base text-ink/75 sm:text-lg">
            Live telemetry for perishable freight moving into Melbourne —
            temperature, humidity, location, and spoilage risk in one ops view.
          </p>

          <div className="mt-6 flex flex-wrap items-center gap-x-5 gap-y-2 font-sans text-sm text-ink/70">
            <span>
              Stream:{" "}
              <strong className={connected ? "text-chill" : "text-warn"}>
                {connected ? "live" : "reconnecting"}
              </strong>
            </span>
            <span>
              API:{" "}
              <strong className={health?.status === "ok" ? "text-chill" : "text-warn"}>
                {health?.status ?? "…"}
              </strong>
            </span>
            <span>
              At risk:{" "}
              <strong className={riskCount > 0 ? "text-risk" : "text-ink"}>
                {riskCount}
              </strong>
            </span>
          </div>
        </header>

        {error && (
          <p className="mb-6 border border-risk/30 bg-risk/5 px-4 py-3 font-sans text-sm text-risk">
            {error}
          </p>
        )}

        {loading ? (
          <p className="font-sans text-ink/60">Loading fleet telemetry…</p>
        ) : (
          <div className="space-y-10">
            <AlertBanner alerts={alerts} onAck={ackAlert} />
            <FleetStatus latest={latest} />
            <div className="grid gap-10 lg:grid-cols-2">
              <TemperatureChart history={history} />
              <RouteMap latest={latest} />
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
