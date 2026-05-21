"use client";

import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { MapContainer, Marker, Polyline, Popup, TileLayer, useMap } from "react-leaflet";
import { useEffect, useMemo } from "react";
import type { Stop, TravelStep } from "@/lib/api";

const SEGMENT_COLOR: Record<TravelStep["mode"], string> = {
  walk: "#6b7280",   // gray-500
  bus: "#d97706",    // amber-600
  subway: "#2e86c1", // accent-dark blue
  rail: "#059669",   // emerald-600
};

function numberedIcon(n: number): L.DivIcon {
  return L.divIcon({
    className: "",
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    html: `<div style="
      display:flex;align-items:center;justify-content:center;
      width:28px;height:28px;border-radius:9999px;
      background:#1a2438;color:#fff;font-weight:700;font-size:13px;
      box-shadow:0 1px 3px rgba(0,0,0,.3);border:2px solid #fff;
    ">${n}</div>`,
  });
}

function FitBounds({ points }: { points: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    if (points.length === 0) return;
    map.fitBounds(points as L.LatLngBoundsLiteral, { padding: [40, 40] });
  }, [map, points]);
  return null;
}

export default function ItineraryMapInner({
  stops,
  routeGeometry,
  closeLoop,
}: {
  stops: Stop[];
  routeGeometry: [number, number][] | null;
  closeLoop: boolean;
}) {
  const points = useMemo<[number, number][]>(
    () =>
      stops
        .filter((s) => s.latitude != null && s.longitude != null)
        .map((s) => [s.latitude!, s.longitude!]),
    [stops],
  );

  // Gather any per-step geometry across all stops. Present only when the
  // route came from Google Routes (transit / fallback non-transit). OSRM
  // legs ship with empty steps.
  const segments = useMemo(() => {
    const out: { mode: TravelStep["mode"]; coords: [number, number][] }[] = [];
    for (const s of stops) {
      for (const step of s.travel_steps_from_prev ?? []) {
        if (step.geometry && step.geometry.length > 1) {
          out.push({ mode: step.mode, coords: step.geometry });
        }
      }
    }
    return out;
  }, [stops]);

  const hasSegments = segments.length > 0;
  // Single-color fallback when we can't split: prefer OSRM road geometry,
  // otherwise straight lines between stops.
  const fallbackLine =
    routeGeometry && routeGeometry.length > 1 ? routeGeometry : points;

  if (points.length === 0) {
    return (
      <div className="flex h-[28rem] items-center justify-center rounded border border-ink/10 bg-paper text-sm text-ink/50">
        No stops with coordinates to plot.
      </div>
    );
  }

  return (
    <MapContainer
      center={points[0]}
      zoom={14}
      scrollWheelZoom
      className="h-[28rem] w-full overflow-hidden rounded-lg border border-ink/10"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {hasSegments ? (
        segments.map((seg, i) => (
          <Polyline
            key={i}
            positions={seg.coords}
            pathOptions={{
              color: SEGMENT_COLOR[seg.mode],
              weight: seg.mode === "walk" ? 3 : 5,
              opacity: seg.mode === "walk" ? 0.75 : 1,
              dashArray: seg.mode === "walk" ? "2 6" : undefined,
            }}
          />
        ))
      ) : (
        <Polyline positions={fallbackLine} pathOptions={{ color: "#5DADE2", weight: 4 }} />
      )}
      {closeLoop && points.length > 1 && (
        <Polyline
          positions={[points[points.length - 1], points[0]]}
          pathOptions={{
            color: "#5DADE2",
            weight: 3,
            opacity: 0.6,
            dashArray: "6 8",
          }}
        />
      )}
      {stops.map((s, i) =>
        s.latitude != null && s.longitude != null ? (
          <Marker key={`${s.place_id}-${i}`} position={[s.latitude, s.longitude]} icon={numberedIcon(i + 1)}>
            <Popup>
              <strong>{s.name}</strong>
              {s.rating != null && (
                <>
                  <br />★ {s.rating.toFixed(1)}
                </>
              )}
            </Popup>
          </Marker>
        ) : null,
      )}
      <FitBounds points={points} />
    </MapContainer>
  );
}
