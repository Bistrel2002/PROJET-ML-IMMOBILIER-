"use client";

import { useEffect, useState } from "react";
import { API_BASE_URL } from "@/lib/constants";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { ArrowUpRight, Building2, Home as HomeIcon } from "lucide-react";

interface DashboardData {
  kpis: {
    median_price: string;
    mean_price: string;
    prix_m2: string;
    ads_count: string;
    mae: string;
    r2_pct: string;
  };
  chart_data: any[];
  alerts: { zone: string; change_pct: string; timeframe: string; reason: string; color_theme: string }[];
  active_markets: { type: string; change_per_year: string; icon: string; price: string; location: string; confidence: number; color_theme: string }[];
}

interface DashboardOptions {
  property_types: string[];
  regions: string[];
}

export default function HomeDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [options, setOptions] = useState<DashboardOptions | null>(null);
  const [propertyType, setPropertyType] = useState("Tous");
  const [region, setRegion] = useState("France entière");

  // Load dropdown options once
  useEffect(() => {
    fetch(`${API_BASE_URL}/api/analytics/dashboard/options`)
      .then(res => res.json())
      .then(setOptions)
      .catch(console.error);
  }, []);

  // Load dashboard data on filter change
  useEffect(() => {
    fetch(`${API_BASE_URL}/api/analytics/dashboard?type=${propertyType}&region=${region}`)
      .then(res => res.json())
      .then(setData)
      .catch(console.error);
  }, [propertyType, region]);

  if (!data) {
    return <div className="flex h-full items-center justify-center text-slate-400">Chargement du tableau de bord...</div>;
  }

  if (!data.kpis) {
    return <div className="flex h-full items-center justify-center text-red-400">Aucune donnée disponible. Vérifiez que les fichiers CSV sont présents dans data/clean/.</div>;
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
            {options ? options.property_types.map(t => (
              <option key={t} value={t}>{t}</option>
            )) : (
              <>
                <option value="Tous">Tous</option>
                <option value="Maison">Maison</option>
                <option value="Appartement">Appartement</option>
              </>
            )}
          </select>
          <select 
            value={region}
            onChange={(e) => setRegion(e.target.value)}
            className="bg-slate-900 border-b border-slate-700 text-white text-sm py-1 pr-6 focus:outline-none focus:border-brand-green">
            {options ? options.regions.map(r => (
              <option key={r} value={r}>{r}</option>
            )) : (
              <>
                <option value="France entière">France entière</option>
              </>
            )}
          </select>
        </div>
      </div>

      {/* 4-Column KPIs */}
      <div className="grid grid-cols-4 gap-8">
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 font-sans">Prix Médian</h2>
          <div className="text-3xl font-medium text-white mb-1">{data.kpis.median_price} €</div>
          <div className="text-sm text-slate-400 flex items-center">
            Données réelles filtrées
          </div>
        </div>
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 font-sans">Prix Moyen</h2>
          <div className="text-3xl font-medium text-white mb-1">{data.kpis.mean_price} €</div>
          <div className="text-sm text-slate-400 flex items-center">
            Moyenne arithmétique
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
          <div className="text-3xl font-medium text-white mb-1">{data.kpis.r2_pct ?? "76.8"}%</div>
          <div className="text-sm text-brand-green flex items-center">
            MAE : {data.kpis.mae} €
          </div>
        </div>
      </div>

      {/* Middle Row: Chart & Alerts */}
      <div className="grid lg:grid-cols-3 gap-12">
        {/* Chart */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">Distribution des prix — Mars 2026</h2>
            <div className="flex items-center gap-2 text-xs text-slate-400 font-medium">
              <span>Nombre d&apos;annonces par tranche</span>
            </div>
          </div>
          
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.chart_data} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" />
                <XAxis dataKey="bracket" stroke="#94a3b8" fontSize={10} tickLine={false} axisLine={false} angle={-20} textAnchor="end" height={50} />
                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '4px', color: '#f8fafc' }}
                  formatter={(value: any) => [`${value} annonces`, 'Nombre']}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {data.chart_data.map((_: any, index: number) => (
                    <Cell key={`cell-${index}`} fill="#10b981" fillOpacity={0.8} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Alerts */}
        <div className="space-y-4">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">Alertes & Insights</h2>
            <span className="text-xs font-medium text-brand-purple bg-brand-purple/10 border border-brand-purple/20 px-2 py-0.5 rounded">XGBoost</span>
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
                  <span className={`text-xs font-medium text-brand-purple bg-brand-purple/10 px-2 py-0.5 rounded`}>{market.change_per_year}</span>
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
