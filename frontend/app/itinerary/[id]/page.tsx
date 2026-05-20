"use client";

import { useQuery } from "@tanstack/react-query";
import { use } from "react";
import { api, formatMinutes, type Itinerary } from "@/lib/api";
import { ItineraryMap } from "@/components/itinerary-map";

const MODE_VERB: Record<Itinerary["transit_mode"], string> = {
  walking: "walk",
  driving: "drive",
  bicycling: "ride",
  transit: "transit",
};

// Threshold above which the day starts to feel unreasonable for the given mode.
const TOO_LONG_MINUTES: Record<Itinerary["transit_mode"], number> = {
  walking: 4 * 60,
  bicycling: 5 * 60,
  driving: 5 * 60,
  transit: 4 * 60,
};

export default function ItineraryPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data, isLoading, error } = useQuery<Itinerary>({
    queryKey: ["itinerary", id],
    queryFn: () => api.get(`/itineraries/${id}`),
  });

  if (isLoading) return <main className="p-8 text-ink/60">Loading…</main>;
  if (error || !data) return <main className="p-8">Could not load itinerary.</main>;

  const verb = MODE_VERB[data.transit_mode];
  const tooLong = data.total_travel_minutes > TOO_LONG_MINUTES[data.transit_mode];

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <header className="mb-6">
        <h1 className="font-display text-3xl tracking-tight">
          {data.title ?? `Day from ${data.start_loc}`}
        </h1>
        <p className="mt-1 text-ink/70">
          {data.stops.length} stops · {data.transit_mode}
          {data.total_travel_minutes > 0 && (
            <>
              {" · "}
              <span className="font-medium text-ink">
                {formatMinutes(data.total_travel_minutes)} total {verb}ing
              </span>
            </>
          )}
        </p>
        {tooLong && (
          <div className="mt-3 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">
            Heads up — that&apos;s a lot of {verb}ing for one day. Consider shrinking the
            radius, dropping stops, or switching transit mode.
          </div>
        )}
      </header>

      <div className="grid gap-6 md:grid-cols-[1fr_2fr]">
        <ol className="flex flex-col gap-0">
          {data.stops.map((s, idx) => (
            <li key={`${s.place_id}-${idx}`}>
              {s.travel_minutes_from_prev != null && (
                <div className="ml-4 flex items-center gap-2 py-1.5 text-xs text-ink/50">
                  <span className="h-4 w-px bg-ink/20" />
                  <span>↓ {formatMinutes(s.travel_minutes_from_prev)} {verb}</span>
                </div>
              )}
              <div className="rounded-lg border border-ink/10 bg-white p-3 shadow-sm">
                <div className="text-xs text-ink/50">Stop {s.position + 1}</div>
                <div className="font-medium">{s.name}</div>
                {s.rating != null && (
                  <div className="text-sm text-ink/60">★ {s.rating.toFixed(1)}</div>
                )}
              </div>
            </li>
          ))}
        </ol>
        <ItineraryMap stops={data.stops} routeGeometry={data.route_geometry} />
      </div>
    </main>
  );
}
