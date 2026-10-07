import { useEffect, useState } from "react";

export function useCountdown(cutoff: string | undefined) {
    const end = cutoff ? new Date(cutoff).getTime() : null;
    const [now, setNow] = useState(() => Date.now())

    useEffect(() => {
        const id = setInterval(() => setNow(Date.now()), 250);
        return () => clearInterval(id);
    }, [])

    const msLeft = end === null ? 0 : Math.max(0, end - now);

    return { msLeft, finished: msLeft === 0 };
}

export function formatTime(ms: number) {
  const totalSeconds = Math.ceil(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}