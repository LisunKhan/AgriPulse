"use client";

import type { AlertRecord } from "@/lib/types";

type Props = {
  alerts: AlertRecord[];
  onAck: (publicId: string) => Promise<void>;
};

export function AlertBanner({ alerts, onAck }: Props) {
  if (alerts.length === 0) {
    return (
      <section className="animate-rise border-b border-line pb-4">
        <p className="font-sans text-sm text-ink/70">
          Cold-chain clear — no open spoilage alerts.
        </p>
      </section>
    );
  }

  return (
    <section className="animate-slide-down space-y-3 border-b border-line pb-5">
      <div className="flex items-baseline justify-between gap-4">
        <h2 className="font-display text-2xl tracking-tight text-risk">
          Active alerts
        </h2>
        <span className="font-sans text-sm text-ink/60">{alerts.length} open</span>
      </div>
      <ul className="space-y-2">
        {alerts.slice(0, 4).map((alert) => (
          <li
            key={alert.public_id}
            className="flex flex-col gap-3 border border-risk/25 bg-risk/5 px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
          >
            <div>
              <p className="font-sans text-sm font-semibold text-ink">
                {alert.device_id} · {alert.alert_type.replaceAll("_", " ")}
              </p>
              <p className="mt-1 font-sans text-sm text-ink/75">{alert.message}</p>
            </div>
            <button
              type="button"
              onClick={() => void onAck(alert.public_id)}
              className="shrink-0 border border-ink/20 bg-mist px-3 py-2 font-sans text-sm text-ink transition hover:border-ink/40 hover:bg-white"
            >
              Acknowledge
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
