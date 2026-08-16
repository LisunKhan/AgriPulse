"use client";

import { useMemo } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { asNumber } from "@/lib/format";
import type { TelemetryRecord } from "@/lib/types";

type Props = {
  history: TelemetryRecord[];
};

const COLORS = ["#2f7f86", "#3f7d5a", "#c9852c"];

export function TemperatureChart({ history }: Props) {
  const { data, deviceIds } = useMemo(() => {
    const devices = Array.from(new Set(history.map((h) => h.device_id))).sort();
    const byTime = new Map<string, Record<string, number | string>>();

    const chronological = [...history].reverse();
    for (const row of chronological) {
      const tick = new Date(row.recorded_at).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
      const key = `${tick}-${row.recorded_at}`;
      const existing = byTime.get(key) ?? { time: tick };
      existing[row.device_id] = asNumber(row.temperature_c);
      byTime.set(key, existing);
    }

    const rows = Array.from(byTime.values()).slice(-40);
    return { data: rows, deviceIds: devices };
  }, [history]);

  return (
    <section className="animate-rise" style={{ animationDelay: "140ms" }}>
      <div className="mb-4 flex items-end justify-between gap-3">
        <h2 className="font-display text-2xl tracking-tight text-ink">
          Temperature trend
        </h2>
        <p className="font-sans text-sm text-ink/60">Safe band 2–8°C</p>
      </div>
      <div className="h-72 w-full border-t border-line pt-4">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid stroke="rgba(20,38,28,0.08)" vertical={false} />
            <XAxis
              dataKey="time"
              tick={{ fill: "rgba(20,38,28,0.55)", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              minTickGap={28}
            />
            <YAxis
              domain={[0, 16]}
              tick={{ fill: "rgba(20,38,28,0.55)", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              unit="°"
            />
            <Tooltip
              contentStyle={{
                background: "#f4faf6",
                border: "1px solid rgba(20,38,28,0.15)",
                borderRadius: 0,
                fontFamily: "inherit",
              }}
            />
            <Legend />
            {deviceIds.map((deviceId, index) => (
              <Line
                key={deviceId}
                type="monotone"
                dataKey={deviceId}
                stroke={COLORS[index % COLORS.length]}
                strokeWidth={2.2}
                dot={false}
                isAnimationActive
                animationDuration={600}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
