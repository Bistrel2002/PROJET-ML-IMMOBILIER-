"use client";

import { useEffect, useState } from "react";
import { API_BASE_URL } from "@/lib/constants";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell
} from "recharts";

interface AnalysisData {
  history_data: any[];
  distribution_data: any[];
  feature_importance: any[];
}

export default function AnalysisPage() {
  const [data, setData] = useState<AnalysisData | null>(null);
  
  // Filter states
  const [zone, setZone] = useState("Nantes 44");
  const [propertyType, setPropertyType] = useState("Appartement");
  const [surfaceMin, setSurfaceMin] = useState("");
  const [surfaceMax, setSurfaceMax] = useState("");
  const [rooms, setRooms] = useState("Toutes pièces");

  useEffect(() => {
    // Basic debounce could be added, but for now we fetch directly
    const params = new URLSearchParams({
      zone,
      type: propertyType,
      smin: surfaceMin,
      smax: surfaceMax,
      rooms
    });

    fetch(`${API_BASE_URL}/api/analytics/analysis?${params.toString()}`)
      .then(res => res.json())
      .then(setData)
      .catch(console.error);
  }, [zone, propertyType, surfaceMin, surfaceMax, rooms]);

  if (!data) {
    return <div className="flex h-full items-center justify-center text-slate-400">Chargement de l'analyse...</div>;
  }

  return (
    <div className="animate-in fade-in duration-700 max-w-7xl mx-auto space-y-10">
      
      {/* Header and Filters */}
      <div>
        <h1 className="text-2xl font-serif font-medium text-white mb-1">Analyse détaillée</h1>
        <p className="text-sm text-slate-400 mb-8">Comprendre les facteurs de variation des prix</p>
        
        <div className="flex flex-wrap gap-4">
          <select 
            value={zone} onChange={(e) => setZone(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-white text-sm rounded px-4 py-2 hover:border-slate-500 focus:outline-none focus:border-brand-green transition-colors">
            <option value="Nantes 44">Nantes 44</option>
            <option value="Paris 75">Paris 75</option>
          </select>
          <select 
            value={propertyType} onChange={(e) => setPropertyType(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-white text-sm rounded px-4 py-2 hover:border-slate-500 focus:outline-none focus:border-brand-green transition-colors">
            <option value="Appartement">Appartement</option>
            <option value="Maison">Maison</option>
          </select>
          <input 
            type="number" 
            value={surfaceMin} onChange={(e) => setSurfaceMin(e.target.value)}
            placeholder="Surface min m²" 
            className="bg-slate-900 border border-slate-700 text-white text-sm rounded px-4 py-2 hover:border-slate-500 focus:outline-none focus:border-brand-green transition-colors w-32" 
          />
          <input 
            type="number" 
            value={surfaceMax} onChange={(e) => setSurfaceMax(e.target.value)}
            placeholder="Surface max m²" 
            className="bg-slate-900 border border-slate-700 text-white text-sm rounded px-4 py-2 hover:border-slate-500 focus:outline-none focus:border-brand-green transition-colors w-32" 
          />
          <select 
            value={rooms} onChange={(e) => setRooms(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-white text-sm rounded px-4 py-2 hover:border-slate-500 focus:outline-none focus:border-brand-green transition-colors">
            <option value="Toutes pièces">Toutes pièces</option>
            <option value="1-2 pièces">1-2 pièces</option>
            <option value="3-4 pièces">3-4 pièces</option>
            <option value="5+ pièces">5+ pièces</option>
          </select>
        </div>
      </div>

      {/* Top Charts Row */}
      <div className="grid lg:grid-cols-3 gap-12">
        
        {/* Main Chart */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">Historique + Intervalle de confiance</h2>
            <div className="flex items-center gap-2 text-xs text-slate-400 font-medium">
              <span>IC 95%</span>
              <div className="w-3 h-3 bg-slate-800 rounded-sm"></div>
            </div>
          </div>
          <div className="h-[280px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.history_data} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
                {/* Confidence Interval Area */}
                <Area type="monotone" dataKey="max" stroke="none" fill="#1e293b" />
                <Area type="monotone" dataKey="min" stroke="none" fill="#0f172a" />
                {/* Main Price Line */}
                <Area 
                  type="monotone" 
                  dataKey="price" 
                  stroke="#10b981" 
                  strokeWidth={2}
                  fill="none" 
                  dot={{ r: 3, fill: '#10b981', strokeWidth: 0 }}
                />
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" />
                <XAxis dataKey="month" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} domain={['dataMin - 100', 'dataMax + 100']} tickFormatter={(v) => `${v}€`} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '4px', color: '#f8fafc' }} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Distribution Chart */}
        <div className="space-y-4">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans text-left">Distribution des prix</h2>
          <div className="h-[280px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.distribution_data} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" />
                <XAxis dataKey="bracket" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} tickFormatter={(v) => `${v}%`} />
                <Tooltip 
                  cursor={{ fill: '#1e293b' }}
                  contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '4px' }}
                />
                <Bar dataKey="pct" radius={[2, 2, 0, 0]}>
                  {data.distribution_data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill="#3b82f6" fillOpacity={0.8} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Bottom Row - Feature Importance */}
      <div className="pt-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">Facteurs influents — Importance des features</h2>
          <span className="text-xs text-brand-purple bg-brand-purple/10 px-2 py-0.5 rounded font-medium border border-brand-purple/20">Random Forest</span>
        </div>
        
        <div className="space-y-4 max-w-4xl">
          {data.feature_importance.map((feat) => (
            <div key={feat.name} className="flex items-center">
              <div className="w-1/4">
                <span className="text-sm font-medium text-white">{feat.name}</span>
              </div>
              <div className="w-2/3 flex items-center">
                <div 
                  className="h-2 rounded-full bg-brand-purple" 
                  style={{ width: `${feat.pct}%` }}
                />
              </div>
              <div className="w-1/12 text-right">
                <span className="text-sm font-medium text-slate-300">{feat.pct}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>
      
    </div>
  );
}
