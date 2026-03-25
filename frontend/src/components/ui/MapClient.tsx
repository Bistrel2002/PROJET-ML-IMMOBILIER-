"use client";

import { useEffect, useState } from "react";
import { API_BASE_URL } from "@/lib/constants";
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";

interface MapDataPoint {
  id: number;
  lat: number;
  lng: number;
  weight: number;
  city: string;
  price: string;
  trend: string;
  confidence: number;
  active: boolean;
}

export default function MapClient() {
  const [points, setPoints] = useState<MapDataPoint[]>([]);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/analytics/heatmap`)
      .then(res => res.json())
      .then(setPoints)
      .catch(console.error);
  }, []);

  return (
    <MapContainer 
      center={[46.603354, 1.888334]} // Center of France
      zoom={6} 
      className="h-full w-full"
      style={{ background: '#0f172a' }} // Dark slate background to match theme
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
      />
      
      {points.map((pt) => {
        // dynamic styling based on trend and activity
        const isPositive = pt.trend.startsWith('+');
        const color = isPositive ? '#10b981' : '#ef4444'; // brand-green or brand-red
        const radius = Math.max(8, Math.min(25, pt.weight / 500)); 

        return (
          <CircleMarker
            key={pt.id}
            center={[pt.lat, pt.lng]}
            radius={radius}
            pathOptions={{
              color: color, 
              fillColor: color,
              fillOpacity: 0.6,
              weight: 2
            }}
          >
            <Popup closeButton={false} autoPan={true}>
              <div className="bg-slate-900 p-4 rounded-lg min-w-[200px]">
                <div className="flex justify-between items-start mb-3">
                  <span className="font-bold text-white text-lg">{pt.city}</span>
                  <span className={`text-xs px-2 py-1 rounded font-bold tracking-wider ${isPositive ? 'bg-brand-green/20 text-brand-green' : 'bg-brand-red/20 text-brand-red'}`}>
                    {pt.trend}
                  </span>
                </div>
                
                <div className="mb-4">
                  <div className="text-sm text-slate-400 font-sans mb-1">Prix moyen estimé</div>
                  <div className="text-2xl font-bold text-white">{pt.price} <span className="text-sm text-slate-500 font-normal">€/m²</span></div>
                </div>
                
                <div className="space-y-1.5 pt-3 border-t border-slate-700/50">
                  <div className="flex justify-between text-xs font-sans">
                    <span className="text-slate-400">Précision Modèle</span>
                    <span className="text-white font-medium">{pt.confidence}%</span>
                  </div>
                  <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                    <div className="bg-brand-blue h-full rounded-full" style={{ width: `${pt.confidence}%` }}></div>
                  </div>
                  <p className="text-[10px] text-slate-500 mt-2 text-right">
                    Source: Random Forest
                  </p>
                </div>
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
