"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, LineChart, Map as MapIcon, Calculator, ActivitySquare } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { name: "Dashboard", href: "/", icon: Home },
  { name: "Analyse Détaillée", href: "/analysis", icon: LineChart },
  { name: "Simulation", href: "/simulation", icon: Calculator },
  { name: "Carte Interactive", href: "/map", icon: MapIcon },
  { name: "Pipeline ML", href: "/pipeline", icon: ActivitySquare },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r border-slate-800 bg-slate-900/50 backdrop-blur-xl">
      <div className="flex h-full flex-col px-4 py-8">
        <div className="mb-12 px-2">
          <span className="text-2xl font-bold tracking-tight text-white">immo<span className="text-brand-green">predict</span></span>
        </div>

        <nav className="flex-1 space-y-1">
          {NAV_ITEMS.slice(0, 3).map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-2 py-2.5 text-sm font-medium transition-all duration-200 border-l-2",
                  isActive
                    ? "border-brand-green text-white bg-slate-800/30"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                )}
              >
                <Icon className={cn("h-4 w-4", isActive ? "text-brand-green" : "text-slate-400")} />
                {item.name}
              </Link>
            );
          })}

          <div className="mt-8 mb-4 px-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Explorer</span>
          </div>

          {NAV_ITEMS.slice(3).map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-2 py-2.5 text-sm font-medium transition-all duration-200 border-l-2",
                  isActive
                    ? "border-brand-green text-white bg-slate-800/30"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                )}
              >
                <Icon className={cn("h-4 w-4", isActive ? "text-brand-green" : "text-slate-400")} />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}
