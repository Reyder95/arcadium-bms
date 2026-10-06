import type { Tier } from "./NetworkModels";

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
    const res = await fetch(`/api${path}`, {
        ...options,
        headers: { "Content-Type": "application/json", ...options.headers },
    });

    if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail ?? `Request failed: ${res.status}`);
    }
    return res.status === 204 ? (undefined as T) : res.json();
}

export function determineTier(tiers: Tier[], rating: number) {
    return tiers.findLastIndex((tier) => rating >= tier.floor) ?? tiers[0];
}

const DIVISIONS = 5;

export function calculateDivision(tiers: Tier[], rating: number, index: number): number | null {
  if (index === tiers.length - 1) return null;

  const floor = tiers[index].floor;
  const divisionWidth = (tiers[index + 1].floor - floor) / DIVISIONS;

  let steps = Math.floor((rating - floor) / divisionWidth);
  steps = Math.max(0, Math.min(steps, DIVISIONS - 1));

  return DIVISIONS - steps;
}

const ROMAN = ["", "I", "II", "III", "IV", "V"];

export function toRoman(n: number): string {
  return ROMAN[n] ?? String(n);
}

export function winRate(wins: number, losses: number): number | null {
  const games = wins + losses;
  if (games === 0) return null;
  return (wins / games) * 100;
}

export function divisionProgress(tiers: Tier[], rating: number, index: number) {
  if (index === tiers.length - 1) return null;   // Grandmaster: no divisions

  const tierFloor = tiers[index].floor;
  const width = (tiers[index + 1].floor - tierFloor) / DIVISIONS;

  let steps = Math.floor((rating - tierFloor) / width);
  steps = Math.max(0, Math.min(steps, DIVISIONS - 1));

  const start = tierFloor + steps * width;
  const end = start + width;
  const percent = Math.max(0, Math.min(100, ((rating - start) / (end - start)) * 100));

  return { start, end, percent };
}