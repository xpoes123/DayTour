"use client";

import dynamic from "next/dynamic";
import type { Stop } from "@/lib/api";

const Inner = dynamic(() => import("./itinerary-map-inner"), {
  ssr: false,
  loading: () => (
    <div className="flex h-[28rem] items-center justify-center rounded border border-ink/10 bg-paper text-sm text-ink/50">
      Loading map…
    </div>
  ),
});

export function ItineraryMap({
  stops,
  routeGeometry,
  closeLoop = false,
}: {
  stops: Stop[];
  routeGeometry: [number, number][] | null;
  closeLoop?: boolean;
}) {
  return <Inner stops={stops} routeGeometry={routeGeometry} closeLoop={closeLoop} />;
}
