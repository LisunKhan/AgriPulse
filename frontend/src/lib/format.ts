export function asNumber(value: unknown, fallback = 0): number {
  const n = typeof value === "number" ? value : Number(value);
  return Number.isFinite(n) ? n : fallback;
}

export function formatFixed(value: unknown, digits: number): string {
  return asNumber(value).toFixed(digits);
}
