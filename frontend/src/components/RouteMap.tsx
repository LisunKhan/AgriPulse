"use client";

import { asNumber } from "@/lib/format";
import type { TelemetryRecord } from "@/lib/types";

type Props = {
  latest: TelemetryRecord[];
};

// Rough Victoria viewport for SVG projection
const BOUNDS = {
  minLat: -39.2,
  maxLat: -34.0,
  minLng: 140.8,
  maxLng: 150.0,
};

const MELBOURNE = { lat: -37.8136, lng: 144.9631 };

function project(lat: number, lng: number) {
  const x =
    ((lng - BOUNDS.minLng) / (BOUNDS.maxLng - BOUNDS.minLng)) * 100;
  const y =
    ((BOUNDS.maxLat - lat) / (BOUNDS.maxLat - BOUNDS.minLat)) * 100;
  return { x: Math.min(98, Math.max(2, x)), y: Math.min(98, Math.max(2, y)) };
}

function markerColor(status: string) {
  if (status === "spoilage_risk") return "#b23a2f";
  if (status === "warning") return "#c9852c";
  return "#2f7f86";
}

export function RouteMap({ latest }: Props) {
  const melbourne = project(MELBOURNE.lat, MELBOURNE.lng);

  return (
    <section className="animate-rise" style={{ animationDelay: "200ms" }}>
      <div className="mb-4 flex items-end justify-between gap-3">
        <h2 className="font-display text-2xl tracking-tight text-ink">
          Transit map
        </h2>
        <p className="font-sans text-sm text-ink/60">Victoria → Melbourne DC</p>
      </div>
      <div className="relative aspect-[4/3] w-full overflow-hidden border border-line bg-gradient-to-br from-[#d7e8df] via-[#cfe0d8] to-[#bdd4cb]">
        <svg viewBox="0 0 100 100" className="h-full w-full" role="img" aria-label="Fleet map">
          <defs>
            <pattern id="dots" width="4" height="4" patternUnits="userSpaceOnUse">
              <circle cx="1" cy="1" r="0.35" fill="rgba(20,38,28,0.12)" />
            </pattern>
          </defs>
          <rect width="100" height="100" fill="url(#dots)" />

          <path
            d="M8 22 C22 18, 35 28, 48 24 C62 20, 74 30, 88 26 L92 78 C70 86, 48 82, 28 88 C18 90, 10 80, 8 22 Z"
            fill="rgba(31,77,56,0.08)"
            stroke="rgba(31,77,56,0.2)"
            strokeWidth="0.4"
          />

          <circle cx={melbourne.x} cy={melbourne.y} r="2.2" fill="#1f4d38" />
          <text
            x={melbourne.x + 2.8}
            y={melbourne.y + 1}
            fontSize="3.2"
            fill="#14261c"
            fontFamily="ui-sans-serif, system-ui, sans-serif"
          >
            Melbourne
          </text>

          {latest.map((truck) => {
            const point = project(asNumber(truck.lat), asNumber(truck.lng));
            return (
              <g key={truck.device_id}>
                <line
                  x1={point.x}
                  y1={point.y}
                  x2={melbourne.x}
                  y2={melbourne.y}
                  stroke="rgba(47,127,134,0.35)"
                  strokeWidth="0.45"
                  strokeDasharray="1.2 1.2"
                />
                <circle
                  cx={point.x}
                  cy={point.y}
                  r="2.4"
                  fill={markerColor(truck.status)}
                  className={truck.status === "spoilage_risk" ? "animate-pulse-soft" : undefined}
                />
                <text
                  x={point.x + 2.6}
                  y={point.y - 1.2}
                  fontSize="2.8"
                  fill="#14261c"
                  fontFamily="ui-sans-serif, system-ui, sans-serif"
                >
                  {truck.device_id}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </section>
  );
}
