import type { Tier, Job, SieglindeCalculations, Match } from "./NetworkModels";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { BetweenTierData, TierProgressData } from "./MiscInterfaces";

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
    if (rating == -1)
      return null;

    return tiers.findLastIndex((tier) => rating >= tier.floor) ?? tiers[0];
}

const DIVISIONS = 5;

export function calculateDivision(tiers: Tier[], rating: number, index: number): number | null {
  if (index === tiers.length - 1) return null;
  if (index === -1) return null;

  const divisionWidth = calculateDivisionWidth(tiers, index);

  let steps = Math.floor((rating - tiers[index].floor) / divisionWidth);
  steps = Math.max(0, Math.min(steps, DIVISIONS - 1));

  return DIVISIONS - steps;
}

export function calculateDivisionWidth(tiers: Tier[], index: number) {
  const floor = tiers[index].floor;
  const divisionWidth = (tiers[index + 1].floor - floor) / DIVISIONS;

  return divisionWidth;
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
  if (rating === -1) return null;   // Unranked

  const tierFloor = tiers[index].floor;
  const width = (tiers[index + 1].floor - tierFloor) / DIVISIONS;

  let steps = Math.floor((rating - tierFloor) / width);
  steps = Math.max(0, Math.min(steps, DIVISIONS - 1));

  const start = tierFloor + steps * width;
  const end = start + width;
  const percent = Math.max(0, Math.min(100, ((rating - start) / (end - start)) * 100));

  return { start, end, percent };
}

export async function waitForJob<T>(jobId: number, intervalMs = 1500, timeoutMs = 60_000): Promise<Job<T>> {
  const started = Date.now();

  while (Date.now() - started < timeoutMs) {
    const job = await api<Job<T>>(`/jobs/${jobId}`);

    if (job.status === "done") return job;
    if (job.status === "failed") throw new Error(job.error ?? "Job failed");

    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }

  throw new Error("Timed out waiting for Bokutachi...")
}

export async function waitForMatch(matchId: number, intervalMs = 1500, timeoutMs = 60_000): Promise<Match> {
  console.log("HI")
  const started = Date.now();

  while (Date.now() - started < timeoutMs) {
    const match = await api<Match>(`/match/${matchId}`);

    if (match.status != "active") return match;

    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }

  throw new Error("Timed out waiting for match...");
}

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatClock(iso: string) {
  return new Date(iso).toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit"
  })
}

export function calculateTimeLeftPercentage(startTime: string | undefined, cutoffTime: string | undefined, msLeft: number | undefined) {
  const start = startTime ? new Date(startTime).getTime() : null;
  const end = cutoffTime ? new Date(cutoffTime).getTime() : null;

  if (!start || !end || msLeft === undefined)
    return 0

  const total = end - start;
  const progressTotal = end - (end - msLeft)

  return Math.min((100 - (progressTotal / total) * 100), 100);
}

export function eloToSieg(elo: number, sieglindeCalcs: SieglindeCalculations) {
  const unified = (elo - sieglindeCalcs.elo_base) / sieglindeCalcs.elo_per_level
  return unified >= 13 ? unified - 12 : unified
}

export function toFixedTruncated(value: number, digits = 2) {
  const factor = 10 ** digits;
  return (Math.trunc(value * factor + Number.EPSILON * factor) / factor).toFixed(digits)
}

export function returnBeginningAndEndRating(starting_rating: number, ending_rating: number, tiers: Tier[]) : BetweenTierData {

  console.log(tiers);

  const startingTierIndex = determineTier(tiers, starting_rating) ?? 0;
  const startingDivision = calculateDivision(tiers, starting_rating, startingTierIndex)
  const startingProgress = divisionProgress(tiers, starting_rating, startingTierIndex)

  const endingTierIndex = determineTier(tiers, ending_rating) ?? 0;
  const endingDivision = calculateDivision(tiers, ending_rating, endingTierIndex);
  const endingProgress = divisionProgress(tiers, ending_rating, endingTierIndex);

  const startingTierProgress : TierProgressData = {
    tierIndex: startingTierIndex,
    division: startingDivision ?? 0,
    progress: startingProgress?.percent ?? 0
  }

  const endingTierProgress : TierProgressData = {
    tierIndex: endingTierIndex,
    division: endingDivision ?? 0,
    progress: endingProgress?.percent ?? 0
  }

  return { startingProgress: startingTierProgress, endingProgress: endingTierProgress }
}

type Step = { tierIndex: number; divisionNumber: number; from: number; to: number };

export function buildSteps(oldR: number, newR: number, tiers: Tier[]): Step[] {

  const steps: Step[] = [];
  const up = newR >= oldR;
  let r = oldR;
  
  while (true) {
    const tierIndex = determineTier(tiers, r) ?? 0;

    if (tierIndex == tiers.length - 1) {
      return [...steps, { tierIndex: tierIndex, divisionNumber: 0, from: 0, to: 0 }]
    }

    const divisionNumber = calculateDivision(tiers, r, tierIndex) ?? 0;
    const progress = divisionProgress(tiers, r, tierIndex);
    if (!progress) return steps;   // unranked / no divisions: nothing to animate

    const { start, end } = progress;
    const pct = (x: number) => ((x - start) / (end - start)) * 100;

    const target = up ? Math.min(newR, end) : Math.max(newR, start);
    steps.push({ tierIndex, divisionNumber, from: pct(r), to: pct(target) });

    if (target === newR) return steps;
    r = up ? end : start - 0.001;
  }
}

export function nextTierInfo(finalRating: number, lastStep: Step, tiers: Tier[]) {
  const progress = divisionProgress(tiers, finalRating, lastStep.tierIndex);
  const nextR = progress?.end;   // null if there are no divisions (Grandmaster/unranked)

  const nextTierIndex = nextR != null ? determineTier(tiers, nextR) : null;
  const nextDivision =
    nextR != null && nextTierIndex != null
      ? calculateDivision(tiers, nextR, nextTierIndex)
      : null;

    return { nextTierIndex, nextDivision }
}