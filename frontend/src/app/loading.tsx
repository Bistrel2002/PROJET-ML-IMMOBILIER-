"use client";

export default function Loading() {
  return (
    <div className="animate-pulse max-w-7xl mx-auto space-y-8">
      {/* Header skeleton */}
      <div>
        <div className="h-7 w-48 bg-slate-800 rounded mb-2" />
        <div className="h-4 w-64 bg-slate-800/60 rounded" />
      </div>

      {/* KPI row skeleton */}
      <div className="grid grid-cols-4 gap-8">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="space-y-3">
            <div className="h-3 w-20 bg-slate-800 rounded" />
            <div className="h-8 w-32 bg-slate-800/80 rounded" />
            <div className="h-3 w-24 bg-slate-800/40 rounded" />
          </div>
        ))}
      </div>

      {/* Chart skeleton */}
      <div className="h-[300px] bg-slate-800/30 rounded border border-slate-800" />

      {/* Bottom row skeleton */}
      <div className="grid grid-cols-3 gap-8">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-48 bg-slate-800/30 rounded border border-slate-800" />
        ))}
      </div>
    </div>
  );
}
