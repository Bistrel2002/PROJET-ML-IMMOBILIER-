"use client";

import { useEffect, useState } from "react";
import { API_BASE_URL } from "@/lib/constants";
import dynamic from "next/dynamic";
import { MapPin, TrendingUp } from "lucide-react";

// Dynamically import MapClient since leaflet requires window
const MapClient = dynamic(() => import("@/components/ui/MapClient"), {
  ssr: false,
  loading: () => (
    <div className="h-full w-full flex items-center justify-center bg-slate-800 text-muted">
      Chargement de la carte...
    </div>
  )
});

interface Alert {
  zone: string;
  current_price: number;
  predicted_growth_1yr_pct: number;
}

export default function MapPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/analytics/invest-alerts`)
      .then(res => res.json())
      .then(setAlerts)
      .catch(console.error);
  }, []);

  return (
    <div className="space-y-8 animate-in fade-in duration-700 h-full flex flex-col">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Carte & Alertes Investissment</h1>
        <p className="text-muted">Explorez la carte de France et identifiez les zones à forte croissance selon l'IA.</p>
      </div>

      <div className="grid lg:grid-cols-4 gap-6 flex-1 min-h-[600px]">
        {/* Map Container */}
        <div className="lg:col-span-3 rounded-2xl overflow-hidden border border-slate-800 shadow-sm relative z-0">
          <MapClient />
        </div>

        {/* Investment Alerts */}
        <div className="space-y-4">
          <h3 className="font-semibold text-white flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-brand-green" />
            Top Alertes IA
          </h3>
          
          <div className="space-y-4">
            {alerts.length > 0 ? alerts.map((alert, idx) => (
              <div key={idx} className="rounded-xl border border-brand-green/30 bg-brand-green/10 p-4">
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-bold text-white flex items-center gap-2">
                    <MapPin className="h-4 w-4 text-brand-green" />
                    {alert.zone}
                  </h4>
                  <span className="bg-brand-green/20 text-brand-green text-xs font-bold px-2 py-1 rounded">
                    +{alert.predicted_growth_1yr_pct.toFixed(1)}%
                  </span>
                </div>
                <p className="text-sm text-slate-300">Prix actuel: {alert.current_price} €/m²</p>
                <p className="text-xs text-muted mt-2">Croissance estimée sur 1 an. Signal fort.</p>
              </div>
            )) : (
              <p className="text-muted text-sm">Chargement des alertes...</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
