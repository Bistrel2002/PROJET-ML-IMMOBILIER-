import React from "react";
import { cn } from "@/lib/utils";

interface KpiCardProps {
  title: string;
  value: string | number;
  icon: React.ElementType;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  className?: string;
  iconClassName?: string;
}

export function KpiCard({ title, value, icon: Icon, trend, className, iconClassName }: KpiCardProps) {
  return (
    <div className={cn("rounded-2xl border border-slate-800 bg-card p-6 shadow-sm", className)}>
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-muted">{title}</p>
        <div className={cn("rounded-lg p-2 bg-slate-800/50", iconClassName)}>
          <Icon className="h-4 w-4 text-slate-300" />
        </div>
      </div>
      <div className="mt-4 flex items-baseline gap-2">
        <h3 className="text-2xl font-bold text-slate-50">{value}</h3>
      </div>
      {trend && (
        <div className="mt-2 flex items-center gap-1.5 text-sm">
          <span
            className={cn(
              "font-medium",
              trend.isPositive ? "text-brand-green" : "text-brand-red"
            )}
          >
            {trend.isPositive ? "+" : "-"}{Math.abs(trend.value)}%
          </span>
          <span className="text-muted">vs last year</span>
        </div>
      )}
    </div>
  );
}
