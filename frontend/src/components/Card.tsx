import { type ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
}

export function Card({ children, className = "" }: CardProps) {
  return (
    <div
      className={`bg-[#0e1420] border border-[#1f2a3d] rounded-2xl p-5 ${className}`}
    >
      {children}
    </div>
  );
}

export function CardHead({
  title,
  right,
}: {
  title: string;
  right?: ReactNode;
}) {
  return (
    <div className="flex items-center justify-between mb-4">
      <h2 className="text-xs font-black uppercase tracking-widest text-[#f1f5f9] m-0">
        {title}
      </h2>
      {right}
    </div>
  );
}

export function Pill({
  children,
  variant = "default",
}: {
  children: ReactNode;
  variant?: "default" | "ok" | "warn" | "danger" | "accent";
}) {
  const colors = {
    default: "bg-white/5 text-[#8b9cb3] border border-[#1f2a3d]",
    ok:      "bg-[#34d399]/10 text-[#34d399] border border-[#34d399]/20",
    warn:    "bg-[#fbbf24]/10 text-[#fbbf24] border border-[#fbbf24]/20",
    danger:  "bg-[#f87171]/10 text-[#f87171] border border-[#f87171]/20",
    accent:  "bg-[#38bdf8]/10 text-[#38bdf8] border border-[#38bdf8]/20",
  };
  return (
    <span
      className={`inline-flex items-center text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full ${colors[variant]}`}
    >
      {children}
    </span>
  );
}
