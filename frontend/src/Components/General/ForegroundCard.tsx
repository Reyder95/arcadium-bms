import type { ReactNode } from "react";
import { cn } from "../../util/helpers";

interface ForegroundCardProps {
    className?: string;
    children?: ReactNode;
}

export default function ForegroundCard({ className, children } : ForegroundCardProps) {
    return (
        <div className={cn("flex flex-col bg-background-dark p-5 rounded-lg border border-zinc-800 min-w-0", className)}>
            {children}
        </div>
    )
}