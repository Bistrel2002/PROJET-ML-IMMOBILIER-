"use client";

import { useEffect, useState } from "react";
import { API_BASE_URL } from "@/lib/constants";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Cell
} from "recharts";

interface AnalysisData {
  type_stats: { type: string; count: number; median: number; prix_min: number; prix_max: number; prix_m2: number }[];
  distribution_data: any[];
  feature_importance: { name: string; pct: number }[];
  top_cities: { city: string; price: number; count: number }[];
  stats?: { count: number; median: number; mean: number; min: number; max: number };
}

interface AnalysisOptions {
  property_types: string[];
  cities: string[];
  rooms: string[];
}

export default function AnalysisPage() {
  const [data, setData] = useState<AnalysisData | null>(null);
  const [options, setOptions] = useState<AnalysisOptions | null>(null);
  
  // Filter states
  const [zone, setZone] = useState("Toutes villes");
  const [propertyType, setPropertyType] = useState("Tous");
  const [surfaceMin, setSurfaceMin] = useState("");
  const [surfaceMax, setSurfaceMax] = useState("");
  const [rooms, setRooms] = useState("Toutes pièces");

  // Load options once
  useEffect(() => {
    fetch(`${API_BASE_URL}/api/analytics/analysis/options`)
      .then(res => res.json())
      .then(setOptions)
      .catch(console.error);
  }, []);

  useEffect(() => {
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
    return <div className="flex h-full items-center justify-center text-slate-400">Chargement de l&apos;analyse...</div>;
  }

  if (data && 'error' in data) {
    return (
      <div className="flex h-full items-center justify-center gap-4">
        <button 
          onClick={() => { setZone("Toutes villes"); setPropertyType("Tous"); setSurfaceMin(""); setSurfaceMax(""); setRooms("Toutes pièces"); }}
          className="px-4 py-2 bg-brand-green/20 border border-brand-green/30 text-brand-green text-sm rounded hover:bg-brand-green/30 transition-colors"
        >
          ← Réinitialiser les filtres
        </button>
        <span className="text-red-400">{(data as any).error}</span>
      </div>
    );
  }

  return (
    <div className="animate-in fade-in duration-700 max-w-7xl mx-auto space-y-10">
      
      {/* Header and Filters */}
      <div>
        <h1 className="text-2xl font-serif font-medium text-white mb-1">Analyse détaillée</h1>
        <p className="text-sm text-slate-400 mb-8">
          Comprendre les facteurs de variation des prix
          {data.stats && <span className="ml-2 text-brand-green">— {data.stats.count} biens analysés</span>}
        </p>
        
        <div className="flex flex-wrap gap-4">
          <select 
            value={zone} onChange={(e) => setZone(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-white text-sm rounded px-4 py-2 hover:border-slate-500 focus:outline-none focus:border-brand-green transition-colors">
            {options ? options.cities.map(c => (
              <option key={c} value={c}>{c}</option>
            )) : (
              <option value="Toutes villes">Toutes villes</option>
            )}
          </select>
          <select 
            value={propertyType} onChange={(e) => setPropertyType(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-white text-sm rounded px-4 py-2 hover:border-slate-500 focus:outline-none focus:border-brand-green transition-colors">
            {options ? options.property_types.map(t => (
              <option key={t} value={t}>{t}</option>
            )) : (
              <>
                <option value="Tous">Tous</option>
                <option value="Appartement">Appartement</option>
                <option value="Maison">Maison</option>
              </>
            )}
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
            {options ? options.rooms.map(r => (
              <option key={r} value={r}>{r}</option>
            )) : (
              <>
                <option value="Toutes pièces">Toutes pièces</option>
                <option value="1-2 pièces">1-2 pièces</option>
                <option value="3-4 pièces">3-4 pièces</option>
                <option value="5+ pièces">5+ pièces</option>
              </>
            )}
          </select>
        </div>
      </div>

      {/* Top Charts Row */}
      <div className="space-y-12">
        
        {/* Main Chart — Per-type stats */}
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">Prix médian par type de bien — Mars 2026</h2>
            <div className="flex items-center gap-2 text-xs text-slate-400 font-medium">
              <span>Données réelles</span>
            </div>
          </div>
          <div className="h-[280px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.type_stats} margin={{ top: 10, right: 30, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" />
                <XAxis dataKey="type" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} tickFormatter={(v) => `${(v/1000).toFixed(0)}k€`} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '4px', color: '#f8fafc' }}
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const d = payload[0].payload;
                      return (
                        <div style={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '4px', padding: '10px 14px' }}>
                          <div style={{ color: '#f8fafc', fontWeight: 600, marginBottom: 6 }}>{d.type}</div>
                          <div style={{ color: '#94a3b8', fontSize: 12 }}>Médian : <span style={{ color: '#10b981' }}>{d.median.toLocaleString()} €</span></div>
                          <div style={{ color: '#94a3b8', fontSize: 12 }}>Min : <span style={{ color: '#f8fafc' }}>{d.prix_min.toLocaleString()} €</span></div>
                          <div style={{ color: '#94a3b8', fontSize: 12 }}>Max : <span style={{ color: '#f8fafc' }}>{d.prix_max.toLocaleString()} €</span></div>
                          <div style={{ color: '#94a3b8', fontSize: 12, marginTop: 4 }}>{d.count} annonces · {d.prix_m2.toLocaleString()} €/m²</div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="median" radius={[4, 4, 0, 0]} barSize={40}>
                  {data.type_stats.map((_: any, index: number) => {
                    const colors = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444'];
                    return <Cell key={`cell-${index}`} fill={colors[index % colors.length]} fillOpacity={0.8} />;
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          {/* Per-type summary below chart */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 pt-2">
            {data.type_stats.map((stat) => (
              <div key={stat.type} className="text-center">
                <div className="text-xs text-slate-400 mb-1">{stat.type}</div>
                <div className="text-sm font-medium text-white">{stat.count} biens</div>
                <div className="text-xs text-slate-500">{stat.prix_m2.toLocaleString()} €/m²</div>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* Bottom Row - Features */}
      <div className="pt-8">
        
        {/* Feature Importance */}
        <div>
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">Facteurs influents — Importance des features</h2>
            <span className="text-xs text-brand-purple bg-brand-purple/10 px-2 py-0.5 rounded font-medium border border-brand-purple/20">XGBoost</span>
          </div>
          
          <div className="space-y-5">
            {data.feature_importance.map((feat) => (
              <div key={feat.name} className="flex items-center">
                <div className="w-1/3">
                  <span className="text-sm font-medium text-white">{feat.name}</span>
                </div>
                <div className="w-1/2 flex items-center pr-4">
                  <div 
                    className="h-2 rounded-full bg-brand-purple" 
                    style={{ width: `${feat.pct}%` }}
                  />
                </div>
                <div className="w-1/6 text-right">
                  <span className="text-sm font-medium text-slate-300">{feat.pct}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
      
    </div>
  );
}
