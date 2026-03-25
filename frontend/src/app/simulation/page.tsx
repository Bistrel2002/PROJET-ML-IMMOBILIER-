"use client";

import { useState } from "react";
import { API_BASE_URL } from "@/lib/constants";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

interface SimulationResult {
  current_estimated_price: number;
  confidence: number;
  price_per_sqm: number;
  projection_temporelle: { period: string; price: number; pct: string }[];
  chart_data: { period: string; price: number }[];
}

export default function SimulationPage() {
  const [formData, setFormData] = useState({
    city: "Nantes, 44000",
    property_type: "Appartement",
    surface_area: 68,
    rooms: 3,
    condition: "Bon état"
  });

  const [result, setResult] = useState<SimulationResult | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSimulate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/predict/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData)
      });
      const data = await res.json();
      setResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-in fade-in duration-700 max-w-7xl mx-auto space-y-10">
      
      {/* Header */}
      <div>
        <h1 className="text-2xl font-serif font-medium text-white mb-1">Simulateur de prédiction</h1>
        <p className="text-sm text-slate-400">Renseignez un bien pour obtenir une projection personnalisée</p>
      </div>

      <div className="grid lg:grid-cols-2 gap-16">
        
        {/* Left Column - Form */}
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-6 font-sans">Paramètres du bien</h2>
          
          <form onSubmit={handleSimulate} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-white mb-2">Ville / code postal</label>
              <select className="w-full bg-slate-900 border border-slate-700 rounded p-2.5 text-white text-sm focus:outline-none focus:border-brand-blue"
                      value={formData.city} onChange={e => setFormData({...formData, city: e.target.value})}>
                <option value="Paris, 75000">Paris, 75000</option>
                <option value="Lyon, 69000">Lyon, 69000</option>
                <option value="Bordeaux, 33000">Bordeaux, 33000</option>
                <option value="Nantes, 44000">Nantes, 44000</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-white mb-2">Type de bien</label>
              <select className="w-full bg-slate-900 border border-slate-700 rounded p-2.5 text-white text-sm focus:outline-none focus:border-brand-blue"
                      value={formData.property_type} onChange={e => setFormData({...formData, property_type: e.target.value})}>
                <option>Appartement</option>
                <option>Maison</option>
              </select>
            </div>
            
            <div className="grid grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-white mb-2">Surface (m²)</label>
                <input type="number" className="w-full bg-slate-900 border border-slate-700 rounded p-2.5 text-white text-sm focus:outline-none focus:border-brand-blue" 
                       value={formData.surface_area} onChange={e => setFormData({...formData, surface_area: Number(e.target.value)})} />
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">Nb pièces</label>
                <input type="number" className="w-full bg-slate-900 border border-slate-700 rounded p-2.5 text-white text-sm focus:outline-none focus:border-brand-blue" 
                       value={formData.rooms} onChange={e => setFormData({...formData, rooms: Number(e.target.value)})} />
              </div>
            </div>
            

            
            <div>
              <label className="block text-sm font-medium text-white mb-2">État du bien</label>
              <select className="w-full bg-slate-900 border border-brand-blue rounded p-2.5 text-white text-sm focus:outline-none focus:border-brand-blue"
                      value={formData.condition} onChange={e => setFormData({...formData, condition: e.target.value})}>
                <option>Bon état</option>
                <option>À rénover</option>
                <option>Neuf</option>
              </select>
            </div>
            
            <div className="pt-2">
              <button disabled={loading} type="submit" className="w-full bg-brand-green hover:bg-emerald-600 text-white font-medium py-3 rounded transition-colors text-sm disabled:opacity-50">
                {loading ? "Calcul en cours..." : "Lancer la prédiction"}
              </button>
            </div>
          </form>
        </div>

        {/* Right Column - Results */}
        <div className={`transition-opacity duration-500 ${result ? 'opacity-100' : 'opacity-30 pointer-events-none'}`}>
          <div className="mb-12">
            <h2 className="text-sm font-medium text-white mb-2">Prix estimé aujourd'hui</h2>
            <div className="text-4xl font-bold text-white mb-1">{result ? Math.round(result.current_estimated_price).toLocaleString() : "236 640"} €</div>
            <div className="text-sm text-slate-400">{result ? result.price_per_sqm.toLocaleString() : "3 480"} €/m² · confiance {result ? result.confidence : "87"}%</div>
          </div>

          <div className="mb-8">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-6 font-sans">Projection temporelle</h2>
            <div className="space-y-4 max-w-sm">
              {(result ? result.projection_temporelle : []).map((proj, idx) => (
                <div key={idx} className="flex justify-between items-center text-sm">
                  <span className="text-white font-medium">Dans {proj.period}</span>
                  <span className="text-slate-300 ml-auto mr-8">{Math.round(proj.price).toLocaleString()} €</span>
                  <span className="text-brand-blue w-12 text-right">{proj.pct}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="h-[200px] w-full mt-4">
            {result && (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={result.chart_data} margin={{ top: 20, right: 20, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" />
                  <XAxis dataKey="period" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} domain={['dataMin - 10000', 'dataMax + 10000']} tickFormatter={(v) => `${(v/1000).toFixed(0)}k`} />
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '4px', color: '#f8fafc' }} />
                  <Line type="monotone" dataKey="price" stroke="#8b5cf6" strokeWidth={2} dot={{ r: 4, fill: '#8b5cf6', strokeWidth: 2, stroke: '#0f172a' }} activeDot={{ r: 6 }} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
          
        </div>

      </div>
    </div>
  );
}
