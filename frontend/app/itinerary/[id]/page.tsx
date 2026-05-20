"use client";

import { useQuery } from "@tanstack/react-query";
import { use } from "react";
import { api, type Itinerary } from "@/lib/api";
import { ItineraryMap } from "@/components/itinerary-map";

export default function ItineraryPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data, isLoading, error } = useQuery<Itinerary>({
    queryKey: ["itinerary", id],
    queryFn: () => api.get(`/itineraries/${id}`),
  });

  if (isLoading) return <main className="p-8">Loading…</main>;
  if (error || !data) return <main className="p-8">Could not load itinerary.</main>;

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <header className="mb-6">
        <h1 className="font-display text-3xl">
          {data.title ?? `Day from ${data.start_loc}`}
        </h1>
        <p className="opacity-70">
          {data.stops.length} stops · {data.transit_mode}
        </p>
      </header>
      <div className="grid gap-6 md:grid-cols-[1fr_2fr]">
        <ol className="flex flex-col gap-3">
          {data.stops.map((s) => (
            <li key={s.place_id} className="rounded border p-3">
              <div className="text-xs opacity-50">Stop {s.position + 1}</div>
              <div className="font-medium">{s.name}</div>
              {s.rating != null && (
                <div className="text-sm opacity-70">★ {s.rating.toFixed(1)}</div>
              )}
            </li>
          ))}
        </ol>
        <ItineraryMap stops={data.stops} />
      </div>
    </main>
  );
}
