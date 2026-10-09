import { cn } from "../../util/helpers";

type ProgressBarProps = {
  value: number;   // 0–100
  className?: string;
  onTransitionEnd: () => void;
  animate: boolean;
  durationMs: number
};

export default function ProgressBar({ value, onTransitionEnd, animate, durationMs, className = "bg-purple-500" }: ProgressBarProps) {
  const percent = Math.min(100, Math.max(0, value));

  return (
    <div
      className="h-2 w-full rounded-full bg-zinc-800 overflow-hidden"
      role="progressbar"
      aria-valuenow={percent}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <div
        onTransitionEnd={onTransitionEnd}
        className={cn(
          "h-full rounded-full",
          className,
          animate && "transition-[width] ease-out"
        )}
        style={{ 
          width: `${percent}%`,
          transitionDuration: animate ? `${durationMs}ms` : "0ms"
         }}
      />
    </div>
  );
}