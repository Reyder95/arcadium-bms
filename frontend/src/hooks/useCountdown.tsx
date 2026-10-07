import { useEffect, useState } from "react";

export function useCountdown(cutoff: string | undefined, startTime: string | undefined) {
    const end = cutoff ? new Date(cutoff).getTime() : null;
    const start = startTime ? new Date(startTime).getTime() : null;
    const [now, setNow] = useState(() => Date.now())

    useEffect(() => {
        const id = setInterval(() => setNow(Date.now()), 250);
        return () => clearInterval(id);
    }, [])

    const msLeft = end === null ? 0 : Math.max(0, end - now);

    const skipEnd = start !== null ? start + 30_000 : null;
    const skipMsLeft = skipEnd !== null ? Math.max(0, skipEnd - now) : 0;
    const skipFinished = skipEnd === null || now >= skipEnd;

    return { msLeft, finished: msLeft === 0, skipFinished, skipMsLeft };
}

export function formatTime(ms: number) {
  const totalSeconds = Math.ceil(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}