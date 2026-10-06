type ProgressBarProps = {
  value: number;   // 0–100
  className?: string;
};

export default function ProgressBar({ value, className = "bg-purple-500" }: ProgressBarProps) {
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
        className={`h-full rounded-full transition-[width] duration-500 ease-out ${className}`}
        style={{ width: `${percent}%` }}
      />
    </div>
  );
}