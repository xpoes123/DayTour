"use client";

import { useEffect, useRef } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import type { Stop } from "@/lib/api";

const TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN ?? "";

export function ItineraryMap({ stops }: { stops: Stop[] }) {
  const ref = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);

  useEffect(() => {
    if (!ref.current || !TOKEN) return;
    mapboxgl.accessToken = TOKEN;

    const points = stops
      .filter((s) => s.latitude != null && s.longitude != null)
      .map((s) => [s.longitude!, s.latitude!] as [number, number]);

    if (points.length === 0) return;

    const map = new mapboxgl.Map({
      container: ref.current,
      style: "mapbox://styles/mapbox/streets-v12",
      center: points[0],
      zoom: 13,
    });
    mapRef.current = map;

    stops.forEach((s, i) => {
      if (s.latitude == null || s.longitude == null) return;
      const el = document.createElement("div");
      el.className =
        "flex h-7 w-7 items-center justify-center rounded-full bg-ink text-paper text-sm font-bold";
      el.textContent = String(i + 1);
      new mapboxgl.Marker(el)
        .setLngLat([s.longitude, s.latitude])
        .setPopup(new mapboxgl.Popup().setText(s.name))
        .addTo(map);
    });

    map.on("load", () => {
      map.addSource("route", {
        type: "geojson",
        data: {
          type: "Feature",
          properties: {},
          geometry: { type: "LineString", coordinates: points },
        },
      });
      map.addLayer({
        id: "route",
        type: "line",
        source: "route",
        paint: { "line-color": "#bb9af7", "line-width": 4 },
      });

      const b = points.reduce(
        (bb, p) => bb.extend(p),
        new mapboxgl.LngLatBounds(points[0], points[0]),
      );
      map.fitBounds(b, { padding: 60 });
    });

    return () => map.remove();
  }, [stops]);

  if (!TOKEN) {
    return (
      <div className="flex h-96 items-center justify-center rounded border text-sm opacity-60">
        Set NEXT_PUBLIC_MAPBOX_TOKEN to render the map.
      </div>
    );
  }

  return <div ref={ref} className="h-[28rem] w-full rounded border" />;
}
