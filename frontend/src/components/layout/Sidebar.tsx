"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, LineChart, Map as MapIcon, Calculator, ActivitySquare, Menu, X } from "lucide-react";
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
  const [mobileOpen, setMobileOpen] = useState(false);

  const navContent = (
    <div className="flex h-full flex-col px-4 py-8">
      <div className="mb-12 px-2 flex justify-between items-center">
        <span className="text-2xl font-bold tracking-tight text-white">immo<span className="text-emerald-400">predict</span></span>
        {/* Close button for mobile */}
        <button 
          onClick={() => setMobileOpen(false)} 
          className="lg:hidden text-slate-400 hover:text-white"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      <nav className="flex-1 space-y-1">
        {NAV_ITEMS.slice(0, 3).map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setMobileOpen(false)}
              className={cn(
                "flex items-center gap-3 px-2 py-2.5 text-sm font-medium transition-all duration-200 border-l-2",
                isActive
                  ? "border-emerald-400 text-white bg-slate-800/30"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              )}
            >
              <Icon className={cn("h-4 w-4", isActive ? "text-emerald-400" : "text-slate-400")} />
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
              onClick={() => setMobileOpen(false)}
              className={cn(
                "flex items-center gap-3 px-2 py-2.5 text-sm font-medium transition-all duration-200 border-l-2",
                isActive
                  ? "border-emerald-400 text-white bg-slate-800/30"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              )}
            >
              <Icon className={cn("h-4 w-4", isActive ? "text-emerald-400" : "text-slate-400")} />
              {item.name}
            </Link>
          );
        })}
      </nav>
    </div>
  );

  return (
    <>
      {/* Mobile hamburger button */}
      <button
        onClick={() => setMobileOpen(true)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 rounded-lg bg-slate-800 border border-slate-700 text-white"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div 
          className="lg:hidden fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar — desktop: always visible, mobile: slide-in */}
      <aside className={cn(
        "fixed left-0 top-0 z-50 h-screen w-64 border-r border-slate-800 bg-slate-900/95 backdrop-blur-xl transition-transform duration-300",
        mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
      )}>
        {navContent}
      </aside>
    </>
  );
}
