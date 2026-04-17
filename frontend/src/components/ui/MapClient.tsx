"use client";

import { useEffect, useState } from "react";
import { API_BASE_URL } from "@/lib/constants";
import { MapContainer, TileLayer, CircleMarker, Tooltip } from "react-leaflet";
import "leaflet/dist/leaflet.css";

interface MapDataPoint {
  id: number;
  lat: number;
  lng: number;
  weight: number;
  price_m2: number;
  city: string;
  price: string;
  trend: string;
  tier: "cheap" | "mid" | "expensive";
  count: number;
  active: boolean;
}

const TIER_COLORS = {
  cheap: "#10b981",     // green
  mid: "#eab308",       // yellow
  expensive: "#ef4444", // red
};

const TIER_LABELS = {
  cheap: "Abordable",
  mid: "Intermédiaire",
  expensive: "Élevé",
};

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
      center={[46.603354, 1.888334]}
      zoom={6} 
      className="h-full w-full"
      style={{ background: '#0f172a' }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
      />
      
      {points.map((pt) => {
        const color = TIER_COLORS[pt.tier] || "#10b981";
        const radius = Math.max(8, Math.min(22, pt.weight / 400)); 

        return (
          <CircleMarker
            key={pt.id}
            center={[pt.lat, pt.lng]}
            radius={radius}
            pathOptions={{
              color: color, 
              fillColor: color,
              fillOpacity: 0.5,
              weight: 2
            }}
            eventHandlers={{
              mouseover: (e) => { e.target.setStyle({ fillOpacity: 0.9, weight: 3 }); },
              mouseout: (e) => { e.target.setStyle({ fillOpacity: 0.5, weight: 2 }); },
            }}
          >
            <Tooltip 
              direction="top" 
              offset={[0, -10]} 
              opacity={1}
              className="custom-tooltip"
            >
              <div style={{ 
                backgroundColor: '#0f172a', 
                border: `1px solid ${color}40`,
                borderRadius: '8px', 
                padding: '10px 14px',
                minWidth: '180px',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <span style={{ color: '#f8fafc', fontWeight: 700, fontSize: '14px' }}>
                    {pt.city}
                  </span>
                  <span style={{ 
                    color: color, 
                    fontSize: '10px', 
                    fontWeight: 600, 
                    backgroundColor: `${color}20`,
                    padding: '2px 6px',
                    borderRadius: '4px',
                  }}>
                    {TIER_LABELS[pt.tier]}
                  </span>
                </div>
                <div style={{ color: color, fontSize: '20px', fontWeight: 700, marginBottom: '4px' }}>
                  {pt.price} <span style={{ color: '#64748b', fontSize: '12px', fontWeight: 400 }}>€/m²</span>
                </div>
                <div style={{ color: '#94a3b8', fontSize: '11px' }}>
                  {pt.trend}
                </div>
              </div>
            </Tooltip>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
