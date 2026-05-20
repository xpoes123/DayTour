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

export function ItineraryMap({ stops }: { stops: Stop[] }) {
  return <Inner stops={stops} />;
}
