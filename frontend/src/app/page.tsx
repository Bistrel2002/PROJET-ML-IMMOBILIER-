"use client";

import { useEffect, useState } from "react";
import { API_BASE_URL } from "@/lib/constants";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { ArrowUpRight, Building2, Home as HomeIcon } from "lucide-react";

interface DashboardData {
  kpis: {
    median_price: string;
    trend_1yr: string;
    pred_6mo: string;
    pred_6mo_pct: string;
    ads_count: string;
    mae: string;
  };
  chart_data: any[];
  alerts: { zone: string; change_pct: string; timeframe: string; reason: string; color_theme: string }[];
  active_markets: { type: string; change_per_year: string; icon: string; price: string; location: string; confidence: number; color_theme: string }[];
}

export default function HomeDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [propertyType, setPropertyType] = useState("Maison");
  const [region, setRegion] = useState("France entière");

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/analytics/dashboard?type=${propertyType}&region=${region}`)
      .then(res => res.json())
      .then(setData)
      .catch(console.error);
  }, [propertyType, region]);

  if (!data) {
    return <div className="flex h-full items-center justify-center text-slate-400">Chargement du tableau de bord...</div>;
  }

  return (
    <div className="animate-in fade-in duration-700 max-w-7xl mx-auto space-y-12">
      
      {/* Header */}
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-serif font-medium text-white mb-1">Tableau de bord</h1>
          <p className="text-sm text-slate-400">Marché immobilier France</p>
        </div>
        <div className="flex gap-4">
          <select 
            value={propertyType}
            onChange={(e) => setPropertyType(e.target.value)}
            className="bg-slate-900 border-b border-slate-700 text-white text-sm py-1 pr-6 focus:outline-none focus:border-brand-green">
            <option value="Maison">Maison</option>
            <option value="Appartement">Appartement</option>
          </select>
          <select 
            value={region}
            onChange={(e) => setRegion(e.target.value)}
            className="bg-slate-900 border-b border-slate-700 text-white text-sm py-1 pr-6 focus:outline-none focus:border-brand-green">
            <option value="France entière">France entière</option>
            <option value="Île-de-France">Île-de-France</option>
          </select>
        </div>
      </div>

      {/* 4-Column KPIs */}
      <div className="grid grid-cols-4 gap-8">
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 font-sans">Prix Médian</h2>
          <div className="text-3xl font-medium text-white mb-1">{data.kpis.median_price} €/m²</div>
          <div className="text-sm text-brand-green flex items-center">
            ↑ {data.kpis.trend_1yr} sur 1 an
          </div>
        </div>
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 font-sans">Prédiction 6 Mois</h2>
          <div className="text-3xl font-medium text-white mb-1">{data.kpis.pred_6mo} €/m²</div>
          <div className="text-sm text-brand-purple flex items-center">
            ↑ {data.kpis.pred_6mo_pct} prédit
          </div>
        </div>
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 font-sans">Annonces Analysées</h2>
          <div className="text-3xl font-medium text-white mb-1">{data.kpis.ads_count}</div>
          <div className="text-sm text-slate-400 flex items-center">
            Leboncoin — mars 2026
          </div>
        </div>
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 font-sans">Précision Modèle</h2>
          <div className="text-3xl font-medium text-white mb-1">91.3%</div>
          <div className="text-sm text-brand-green flex items-center">
            MAE : {data.kpis.mae} €/m²
          </div>
        </div>
      </div>

      {/* Middle Row: Chart & Alerts */}
      <div className="grid lg:grid-cols-3 gap-12">
        {/* Chart */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">Évolution des prix — Historique + Prévision</h2>
            <div className="flex items-center gap-4 text-xs font-medium">
              <div className="flex items-center gap-2 text-slate-300">
                <div className="w-4 h-0.5 bg-brand-green"></div>
                Historique
              </div>
              <div className="flex items-center gap-2 text-slate-300">
                <div className="w-4 h-0.5 bg-brand-purple border-t border-dashed border-brand-purple"></div>
                Prévision
              </div>
            </div>
          </div>
          
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.chart_data} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" />
                <XAxis dataKey="month" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} domain={['dataMin - 50', 'dataMax + 50']} tickFormatter={(v) => `${v}€`} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '4px', color: '#f8fafc' }}
                />
                <Line type="monotone" dataKey="price" stroke="#10b981" strokeWidth={2} dot={false} activeDot={{ r: 4, fill: '#10b981' }} />
                <Line type="monotone" dataKey="predictedPrice" stroke="#8b5cf6" strokeDasharray="5 5" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Alerts */}
        <div className="space-y-4">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">Alertes Investissement</h2>
            <span className="text-xs font-medium text-brand-purple bg-brand-purple/10 border border-brand-purple/20 px-2 py-0.5 rounded">3 nouvelles</span>
          </div>

          <div className="space-y-3">
            {data.alerts.map((alert, idx) => {
              const theme = alert.color_theme === "purple" ? "brand-purple" : "brand-red";
              return (
                <div key={idx} className={`bg-${theme}/10 border border-${theme}/30 rounded p-4`}>
                  <div className="flex items-center gap-2 text-sm text-white mb-1">
                    <div className={`w-1.5 h-1.5 rounded-full bg-${theme}`}></div>
                    <span className="font-semibold">{alert.zone}</span> — {alert.reason} <span className={`text-${theme} font-medium`}>{alert.change_pct}</span>
                  </div>
                  <p className={`text-xs text-${theme}/80 ml-3.5`}>{alert.timeframe}</p>
                </div>
              );
            })}
          </div>


        </div>
      </div>

      {/* Bottom Row */}
      <div className="pt-8 space-y-6">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">Marchés les plus actifs</h2>
        
        <div className="grid lg:grid-cols-3 gap-8">
          {data.active_markets.map((market, idx) => {
            const IconComponent = market.icon === "Home" ? HomeIcon : Building2;
            const themeClass = market.color_theme === "green" ? "brand-green" : market.color_theme === "red" ? "brand-red" : "[#f59e0b]";
            return (
              <div key={idx} className="flex flex-col h-full bg-slate-900 border border-slate-800 rounded p-5 relative overflow-hidden">
                <div className="flex justify-between items-start mb-6">
                  <span className={`text-xs font-medium text-${themeClass} bg-${themeClass}/10 border border-${themeClass}/20 px-2 py-0.5 rounded`}>{market.type}</span>
                  <span className={`text-xs font-medium text-brand-${market.color_theme === "red" ? "red" : "purple"} bg-brand-${market.color_theme === "red" ? "red" : "purple"}/10 px-2 py-0.5 rounded`}>{market.change_per_year}</span>
                </div>
                <div className="flex justify-center mb-6">
                  <IconComponent className="h-8 w-8 text-slate-500" />
                </div>
                <div className="mt-auto">
                  <div className="text-xl font-bold text-white mb-1">{market.price} €</div>
                  <div className="text-xs text-slate-400 mb-5">{market.location}</div>
                  
                  <div className="flex justify-between text-xs mb-1">
                    <span className="font-medium text-white">Confiance</span>
                    <span className="text-brand-green font-medium">{market.confidence}%</span>
                  </div>
                  <div className="w-full bg-slate-800 h-1 rounded-full">
                    <div className="bg-brand-green h-1 rounded-full" style={{ width: `${market.confidence}%` }}></div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
      
    </div>
  );
}
