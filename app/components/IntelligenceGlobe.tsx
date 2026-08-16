"use client";

import { useEffect, useRef, useState } from "react";

export type GlobeEvent = {
  id: string;
  region: string;
  title: string;
  status: "CONFIRMED" | "DEVELOPING" | "DISPUTED";
  impact: "POSITIVE" | "NEGATIVE" | "MIXED";
  companies: string[];
};

const REGION_COORDS: Record<string, [number, number]> = {
  INDIA: [22, 79], ASIA: [34, 100], "MIDDLE EAST": [25, 45],
  "UNITED STATES": [38, -97], EUROPE: [50, 10], AFRICA: [2, 20], GLOBAL: [4, 0],
};

const colours = { POSITIVE: "#7cffb0", NEGATIVE: "#ff617d", MIXED: "#f5bd51" };

export default function IntelligenceGlobe({ events, selectedId, onSelect }: { events: GlobeEvent[]; selectedId?: string; onSelect: (event: GlobeEvent) => void }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [paused, setPaused] = useState(false);
  const [hovered, setHovered] = useState<string>();
  const markersRef = useRef<{ event: GlobeEvent; x: number; y: number; visible: boolean }[]>([]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    let raf = 0;
    let angle = -0.35;
    let last = performance.now();

    const draw = (now: number) => {
      const rect = canvas.getBoundingClientRect();
      const dpr = Math.min(devicePixelRatio || 1, 2);
      if (canvas.width !== Math.round(rect.width * dpr) || canvas.height !== Math.round(rect.height * dpr)) {
        canvas.width = Math.round(rect.width * dpr); canvas.height = Math.round(rect.height * dpr);
      }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const w = rect.width, h = rect.height, r = Math.min(w * .3, h * .42), cx = w * .42, cy = h * .52;
      const dt = Math.min(40, now - last); last = now;
      if (!paused) angle += dt * .000055;
      ctx.clearRect(0, 0, w, h);

      const glow = ctx.createRadialGradient(cx - r * .25, cy - r * .2, 0, cx, cy, r * 1.18);
      glow.addColorStop(0, "rgba(84,255,214,.13)"); glow.addColorStop(.66, "rgba(15,64,64,.1)"); glow.addColorStop(1, "rgba(2,10,12,0)");
      ctx.fillStyle = glow; ctx.beginPath(); ctx.arc(cx, cy, r * 1.25, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = "rgba(98,255,226,.35)"; ctx.lineWidth = 1.2; ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.stroke();

      ctx.save(); ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.clip();
      ctx.fillStyle = "rgba(6,24,26,.88)"; ctx.fillRect(cx - r, cy - r, r * 2, r * 2);
      ctx.strokeStyle = "rgba(114,255,222,.13)"; ctx.lineWidth = 1;
      for (let lat = -60; lat <= 60; lat += 30) {
        const y = cy - Math.sin(lat * Math.PI / 180) * r;
        const rx = Math.cos(lat * Math.PI / 180) * r;
        ctx.beginPath(); ctx.ellipse(cx, y, rx, rx * .18, 0, 0, Math.PI * 2); ctx.stroke();
      }
      for (let lon = 0; lon < 180; lon += 30) {
        ctx.beginPath(); ctx.ellipse(cx, cy, Math.abs(Math.cos(angle + lon * Math.PI / 180)) * r, r, 0, 0, Math.PI * 2); ctx.stroke();
      }
      ctx.restore();

      const markers = events.slice(0, 8).map((event) => {
        const [lat, lon] = REGION_COORDS[event.region.toUpperCase()] ?? REGION_COORDS.GLOBAL;
        const lambda = lon * Math.PI / 180 + angle;
        const phi = lat * Math.PI / 180;
        const visible = Math.cos(phi) * Math.cos(lambda) > -.12;
        const x = cx + r * Math.cos(phi) * Math.sin(lambda);
        const y = cy - r * Math.sin(phi);
        return { event, x, y, visible };
      });
      markersRef.current = markers;

      const india = (() => { const [lat, lon] = REGION_COORDS.INDIA; const l = lon * Math.PI / 180 + angle; const p = lat * Math.PI / 180; return { x: cx + r * Math.cos(p) * Math.sin(l), y: cy - r * Math.sin(p), visible: Math.cos(p) * Math.cos(l) > -.12 }; })();
      ctx.setLineDash([4, 6]);
      markers.forEach((marker) => {
        if (!marker.visible || !india.visible || marker.event.region === "INDIA") return;
        ctx.strokeStyle = "rgba(117,255,221,.22)"; ctx.beginPath(); ctx.moveTo(india.x, india.y); ctx.quadraticCurveTo((india.x + marker.x) / 2, Math.min(india.y, marker.y) - 45, marker.x, marker.y); ctx.stroke();
      });
      ctx.setLineDash([]);
      markers.forEach((marker, i) => {
        if (!marker.visible) return;
        const selected = marker.event.id === selectedId || marker.event.id === hovered;
        const pulse = 6 + ((now / 650 + i) % 1) * 16;
        ctx.strokeStyle = colours[marker.event.impact] + (selected ? "bb" : "55"); ctx.beginPath(); ctx.arc(marker.x, marker.y, pulse, 0, Math.PI * 2); ctx.stroke();
        ctx.fillStyle = colours[marker.event.impact]; ctx.shadowColor = colours[marker.event.impact]; ctx.shadowBlur = selected ? 20 : 10; ctx.beginPath(); ctx.arc(marker.x, marker.y, selected ? 6 : 4, 0, Math.PI * 2); ctx.fill(); ctx.shadowBlur = 0;
      });

      ctx.strokeStyle = "rgba(199,255,74,.22)"; ctx.beginPath(); ctx.ellipse(cx, cy, r * 1.3, r * .24, -.12, 0, Math.PI * 2); ctx.stroke();
      raf = requestAnimationFrame(draw);
    };
    raf = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(raf);
  }, [events, paused, hovered, selectedId]);

  const locate = (x: number, y: number) => markersRef.current.filter(m => m.visible).sort((a, b) => Math.hypot(a.x - x, a.y - y) - Math.hypot(b.x - x, b.y - y))[0];
  const point = (event: React.MouseEvent<HTMLCanvasElement>) => { const rect = event.currentTarget.getBoundingClientRect(); return { x: event.clientX - rect.left, y: event.clientY - rect.top }; };

  return <div className="globe-stage">
    <canvas ref={canvasRef} onMouseMove={(e) => { const p = point(e); const hit = locate(p.x, p.y); setHovered(hit && Math.hypot(hit.x - p.x, hit.y - p.y) < 18 ? hit.event.id : undefined); }} onMouseLeave={() => setHovered(undefined)} onClick={(e) => { const p = point(e); const hit = locate(p.x, p.y); if (hit && Math.hypot(hit.x - p.x, hit.y - p.y) < 22) { setPaused(true); onSelect(hit.event); } }} aria-label="Interactive globe of evidence-backed market events" />
    <button className="globe-control" onClick={() => setPaused(v => !v)}>{paused ? "RESUME ROTATION" : "PAUSE ROTATION"}</button>
    <div className="globe-readout"><span>ORBITAL FEED</span><strong>{events.length.toString().padStart(2, "0")}</strong><small>tracked events</small></div>
  </div>;
}
