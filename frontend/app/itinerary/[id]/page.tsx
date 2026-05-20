"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { use, useState } from "react";
import {
  api,
  formatMinutes,
  type Itinerary,
  type Stop,
  type TravelStep,
} from "@/lib/api";
import { ItineraryMap } from "@/components/itinerary-map";

const MODE_VERB: Record<Itinerary["transit_mode"], string> = {
  walking: "walk",
  driving: "drive",
  bicycling: "ride",
  transit: "transit",
};

const TOO_LONG_MINUTES: Record<Itinerary["transit_mode"], number> = {
  walking: 4 * 60,
  bicycling: 5 * 60,
  driving: 5 * 60,
  transit: 4 * 60,
};

const STEP_STYLE: Record<TravelStep["mode"], { bg: string; label: string; icon: string }> = {
  walk: { bg: "bg-ink/10 text-ink/70", label: "Walk", icon: "🚶" },
  bus: { bg: "bg-amber-100 text-amber-900", label: "Bus", icon: "🚌" },
  subway: { bg: "bg-accent/20 text-accent-dark", label: "Subway", icon: "🚇" },
  rail: { bg: "bg-emerald-100 text-emerald-900", label: "Rail", icon: "🚆" },
};

function StepChip({ step }: { step: TravelStep }) {
  const s = STEP_STYLE[step.mode];
  const mins = Math.max(1, Math.round(step.duration_sec / 60));
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${s.bg}`}
    >
      <span aria-hidden>{s.icon}</span>
      <span>{step.label ?? s.label}</span>
      <span className="opacity-70">·</span>
      <span className="tabular-nums">{mins}m</span>
    </span>
  );
}

function StopCard({
  stop,
  rejected,
  onToggle,
}: {
  stop: Stop;
  rejected: boolean;
  onToggle: () => void;
}) {
  return (
    <div
      className={`relative rounded-lg border p-3 shadow-sm transition-opacity ${
        rejected
          ? "border-ink/10 bg-ink/[0.03] opacity-60"
          : "border-ink/10 bg-white"
      }`}
    >
      <button
        type="button"
        onClick={onToggle}
        aria-label={rejected ? "Restore stop" : "Remove stop"}
        className={`absolute right-2 top-2 flex h-6 w-6 items-center justify-center rounded-full text-sm font-semibold transition ${
          rejected
            ? "bg-ink/10 text-ink/60 hover:bg-ink/20"
            : "bg-ink/5 text-ink/40 hover:bg-red-100 hover:text-red-700"
        }`}
        title={rejected ? "Restore" : "Remove"}
      >
        {rejected ? "↺" : "×"}
      </button>
      <div className="text-xs text-ink/50">Stop {stop.position + 1}</div>
      <div className={`font-medium ${rejected ? "line-through" : ""}`}>{stop.name}</div>
      {stop.rating != null && (
        <div className="text-sm text-ink/60">★ {stop.rating.toFixed(1)}</div>
      )}
    </div>
  );
}

export default function ItineraryPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const qc = useQueryClient();
  const { data, isLoading, error } = useQuery<Itinerary>({
    queryKey: ["itinerary", id],
    queryFn: () => api.get(`/itineraries/${id}`),
  });
  const [rejected, setRejected] = useState<Set<string>>(new Set());

  const recompute = useMutation({
    mutationFn: (kept: string[]) =>
      api.post<Itinerary>(`/itineraries/${id}/recompute`, { kept_place_ids: kept }),
    onSuccess: (updated) => {
      setRejected(new Set());
      qc.setQueryData(["itinerary", id], updated);
    },
  });

  if (isLoading) return <main className="p-8 text-ink/60">Loading…</main>;
  if (error || !data) return <main className="p-8">Could not load itinerary.</main>;

  const verb = MODE_VERB[data.transit_mode];
  const tooLong = data.total_travel_minutes > TOO_LONG_MINUTES[data.transit_mode];
  const visibleStops = data.stops.filter((s) => !rejected.has(s.place_id));
  const wouldRemain = visibleStops.length;
  const canRecompute = rejected.size > 0 && wouldRemain >= 2;

  function toggle(placeId: string) {
    setRejected((prev) => {
      const next = new Set(prev);
      if (next.has(placeId)) next.delete(placeId);
      else next.add(placeId);
      return next;
    });
  }

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
          {data.stops.map((s, idx) => {
            const isRejected = rejected.has(s.place_id);
            // Only show the inbound leg label/chips when the stop is kept.
            const showLeg = !isRejected && s.travel_minutes_from_prev != null;
            return (
              <li key={`${s.place_id}-${idx}`}>
                {showLeg && (
                  <div className="ml-4 flex flex-col gap-1 py-2">
                    <div className="flex items-center gap-2 text-xs text-ink/50">
                      <span className="h-4 w-px bg-ink/20" />
                      <span>↓ {formatMinutes(s.travel_minutes_from_prev!)} {verb}</span>
                    </div>
                    {s.travel_steps_from_prev.length > 1 && (
                      <div className="ml-3 flex flex-wrap gap-1">
                        {s.travel_steps_from_prev.map((st, i) => (
                          <StepChip key={i} step={st} />
                        ))}
                      </div>
                    )}
                  </div>
                )}
                <StopCard stop={s} rejected={isRejected} onToggle={() => toggle(s.place_id)} />
              </li>
            );
          })}
        </ol>
        <ItineraryMap stops={visibleStops} routeGeometry={data.route_geometry} />
      </div>

      {rejected.size > 0 && (
        <div className="fixed inset-x-0 bottom-0 z-40 border-t border-ink/10 bg-white/95 px-6 py-3 shadow-lg backdrop-blur">
          <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3">
            <div className="text-sm text-ink/70">
              {rejected.size} stop{rejected.size === 1 ? "" : "s"} removed ·{" "}
              <span className="font-medium text-ink">{wouldRemain} remaining</span>
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setRejected(new Set())}
                className="rounded-md border border-ink/15 px-3 py-1.5 text-sm hover:bg-ink/5"
              >
                Reset
              </button>
              <button
                type="button"
                disabled={!canRecompute || recompute.isPending}
                onClick={() =>
                  recompute.mutate(
                    data.stops
                      .map((s) => s.place_id)
                      .filter((pid) => !rejected.has(pid)),
                  )
                }
                className="rounded-md bg-accent px-4 py-1.5 text-sm font-medium text-white shadow-sm hover:bg-accent-dark disabled:opacity-50"
              >
                {recompute.isPending
                  ? "Recalculating…"
                  : wouldRemain < 2
                  ? "Keep at least 2 stops"
                  : "Recalculate route"}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
