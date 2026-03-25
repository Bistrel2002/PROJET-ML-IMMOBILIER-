"use client";

import { useEffect, useState } from "react";
import { API_BASE_URL } from "@/lib/constants";

interface PipelineData {
  steps: { id: number; title: string; desc: string; status: string; status_format: string }[];
  metrics: { mae: string; rmse: string; r2: string; train: string; test: string };
  stack: { name: string; val: string }[];
  last_run: string;
}

export default function PipelinePage() {
  const [data, setData] = useState<PipelineData | null>(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/analytics/pipeline`)
      .then(res => res.json())
      .then(setData)
      .catch(console.error);
  }, []);

  if (!data) return <div className="flex h-full items-center justify-center text-slate-400">Chargement...</div>;

  return (
    <div className="animate-in fade-in duration-700 max-w-7xl mx-auto">
      <div className="mb-10">
        <h1 className="text-2xl font-serif font-medium text-white mb-1">Pipeline ML</h1>
        <p className="text-sm text-slate-400">Traçabilité complète du pipeline de données</p>
      </div>

      <div className="grid lg:grid-cols-3 gap-16">
        {/* Left Column - Steps */}
        <div className="lg:col-span-2">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-8 font-sans">Étapes du pipeline</h2>
          
          <div className="space-y-8">
            {data.steps.map((step) => {
              const bgClass = step.status_format === "ok" ? "bg-brand-green/20 text-brand-green" 
                : step.status_format === "running" ? "bg-brand-purple/20 text-brand-purple"
                : step.status_format === "deployed" ? "border border-brand-green/30 text-brand-green bg-transparent"
                : "bg-slate-800 text-slate-400";
              
              return (
                <div key={step.id} className="flex items-start justify-between">
                  <div className="flex gap-4">
                    <div className="flex-shrink-0 flex h-8 w-8 items-center justify-center rounded-full bg-brand-green/10 text-brand-green font-medium text-sm">
                      {step.id}
                    </div>
                    <div>
                      <h3 className="text-white font-medium text-sm">{step.title}</h3>
                      <p className="text-xs text-slate-400 mt-1">{step.desc}</p>
                    </div>
                  </div>
                  <div className="ml-4 flex-shrink-0">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-medium uppercase tracking-wider ${bgClass}`}>
                      {step.status}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column - Metrics & Stack */}
        <div className="space-y-12">
          <div>
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-6 font-sans">Métriques du modèle</h2>
            <div className="space-y-4">
              <div className="flex justify-between items-center text-sm">
                <span className="text-white font-medium">MAE</span>
                <span className="text-slate-300">{data.metrics.mae} €/m²</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-white font-medium">RMSE</span>
                <span className="text-slate-300">{data.metrics.rmse} €/m²</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-white font-medium">R² score</span>
                <span className="text-slate-300">{data.metrics.r2}</span>
              </div>
              <div className="flex justify-between items-center text-sm pt-2">
                <span className="text-white font-medium">Données train</span>
                <span className="text-slate-300">{data.metrics.train}</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-white font-medium">Données test</span>
                <span className="text-slate-300">{data.metrics.test}</span>
              </div>
            </div>
          </div>

          <div>
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-6 font-sans">Stack technique</h2>
            <div className="space-y-4">
              {data.stack.map((item, idx) => (
                <div key={idx} className="flex justify-between items-center text-sm">
                  <span className="text-white font-medium">{item.name}</span>
                  <span className="text-slate-300">{item.val}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
      
      {/* Bottom info section */}
      <div className="fixed bottom-6 left-72">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <div className="h-1.5 w-1.5 rounded-full bg-brand-green"></div>
          Pipeline actif — {data.last_run}
        </div>
        <div className="text-[10px] text-slate-500 mt-1">
          Source : Leboncoin scraping
        </div>
      </div>
    </div>
  );
}
