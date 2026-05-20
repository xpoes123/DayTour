"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { use, useMemo, useState } from "react";
import {
  api,
  formatMinutes,
  photoSrc,
  type Alternative,
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

type Change =
  | { kind: "remove" }
  | { kind: "swap"; with: Alternative };

function AlternativesPicker({
  alternatives,
  selected,
  usedElsewhere,
  onPick,
  onClear,
}: {
  alternatives: Alternative[];
  selected: Alternative | null;
  usedElsewhere: Set<string>;
  onPick: (alt: Alternative) => void;
  onClear: () => void;
}) {
  if (alternatives.length === 0) {
    return (
      <div className="mt-2 rounded-md border border-dashed border-ink/15 bg-ink/[0.02] p-2 text-xs text-ink/50">
        No more places within this radius.
      </div>
    );
  }
  return (
    <div className="mt-2 flex flex-col gap-1">
      <div className="text-xs font-medium uppercase tracking-wide text-ink/50">
        {selected ? "Replacing with" : "Replace with"}
      </div>
      <ul className="flex flex-col gap-1">
        {alternatives.map((a) => {
          const isSelected = selected?.place_id === a.place_id;
          const isTaken = !isSelected && usedElsewhere.has(a.place_id);
          return (
            <li key={a.place_id}>
              <button
                type="button"
                disabled={isTaken}
                onClick={() => (isSelected ? onClear() : onPick(a))}
                className={`flex w-full items-center gap-2 rounded-md border px-2 py-1.5 text-left text-sm transition ${
                  isSelected
                    ? "border-accent bg-accent/10"
                    : isTaken
                    ? "cursor-not-allowed border-ink/10 bg-ink/[0.03] text-ink/40"
                    : "border-ink/10 bg-white hover:border-accent/50 hover:bg-accent/5"
                }`}
              >
                <span aria-hidden className="text-xs">
                  {isSelected ? "✓" : "+"}
                </span>
                <span className="flex-1 truncate">{a.name}</span>
                {a.rating != null && (
                  <span className="text-xs text-ink/50">★ {a.rating.toFixed(1)}</span>
                )}
                {isTaken && <span className="text-xs text-ink/40">used</span>}
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function StopCard({
  stop,
  change,
  onRemove,
  onRestore,
}: {
  stop: Stop;
  change: Change | undefined;
  onRemove: () => void;
  onRestore: () => void;
}) {
  const rejected = change !== undefined;
  const img = !rejected ? photoSrc(stop.photo_url) : null;
  return (
    <div
      className={`relative overflow-hidden rounded-lg border shadow-sm transition-colors ${
        rejected ? "border-ink/10 bg-ink/[0.03]" : "border-ink/10 bg-white"
      }`}
    >
      {img && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={img}
          alt=""
          loading="lazy"
          className="h-32 w-full object-cover"
          onError={(e) => {
            (e.currentTarget as HTMLImageElement).style.display = "none";
          }}
        />
      )}
      <div className="relative p-3">
        <button
          type="button"
          onClick={rejected ? onRestore : onRemove}
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
        <div className={`font-medium ${rejected ? "line-through text-ink/60" : ""}`}>
          {stop.name}
        </div>
        {stop.rating != null && (
          <div className="text-sm text-ink/60">★ {stop.rating.toFixed(1)}</div>
        )}
        {change?.kind === "swap" && (
          <div className="mt-2 rounded-md border border-accent/40 bg-accent/10 px-2 py-1.5 text-sm">
            <div className="text-xs uppercase tracking-wide text-accent-dark">Swapping in</div>
            <div className="font-medium text-ink">{change.with.name}</div>
          </div>
        )}
      </div>
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

  const [changes, setChanges] = useState<Map<string, Change>>(new Map());

  // Alternatives are lazy-loaded the first time the user clicks a remove (X).
  const altsQuery = useQuery<Alternative[]>({
    queryKey: ["itinerary-alternatives", id],
    queryFn: () => api.get(`/itineraries/${id}/alternatives`),
    enabled: changes.size > 0,
    staleTime: 5 * 60 * 1000,
  });

  const recompute = useMutation({
    mutationFn: (kept: string[]) =>
      api.post<Itinerary>(`/itineraries/${id}/recompute`, { kept_place_ids: kept }),
    onSuccess: (updated) => {
      setChanges(new Map());
      qc.setQueryData(["itinerary", id], updated);
      qc.invalidateQueries({ queryKey: ["itinerary-alternatives", id] });
    },
  });

  const swappedAltIds = useMemo(() => {
    const s = new Set<string>();
    for (const c of changes.values()) {
      if (c.kind === "swap") s.add(c.with.place_id);
    }
    return s;
  }, [changes]);

  if (isLoading) return <main className="p-8 text-ink/60">Loading…</main>;
  if (error || !data) return <main className="p-8">Could not load itinerary.</main>;

  const verb = MODE_VERB[data.transit_mode];
  const tooLong = data.total_travel_minutes > TOO_LONG_MINUTES[data.transit_mode];

  const visibleStops: Stop[] = data.stops.flatMap((s) => {
    const c = changes.get(s.place_id);
    if (!c) return [s];
    if (c.kind === "swap") {
      // Render the new place at the old position; lat/lon comes from the alternative.
      return [
        {
          ...s,
          place_id: c.with.place_id,
          name: c.with.name,
          latitude: c.with.latitude,
          longitude: c.with.longitude,
          photo_url: c.with.photo_url,
          rating: c.with.rating,
          // Routing info won't be accurate until recompute lands; clear it.
          travel_minutes_from_prev: null,
          travel_steps_from_prev: [],
        },
      ];
    }
    return [];
  });

  const finalPlaceIds = data.stops.flatMap((s) => {
    const c = changes.get(s.place_id);
    if (!c) return [s.place_id];
    if (c.kind === "swap") return [c.with.place_id];
    return [];
  });

  const removeCount = Array.from(changes.values()).filter((c) => c.kind === "remove").length;
  const swapCount = Array.from(changes.values()).filter((c) => c.kind === "swap").length;
  const canApply = changes.size > 0 && finalPlaceIds.length >= 2;

  function markRemove(placeId: string) {
    setChanges((prev) => {
      const next = new Map(prev);
      next.set(placeId, { kind: "remove" });
      return next;
    });
  }

  function restoreOriginal(placeId: string) {
    setChanges((prev) => {
      const next = new Map(prev);
      next.delete(placeId);
      return next;
    });
  }

  function pickAlternative(originalPlaceId: string, alt: Alternative) {
    setChanges((prev) => {
      const next = new Map(prev);
      next.set(originalPlaceId, { kind: "swap", with: alt });
      return next;
    });
  }

  function clearAlternative(originalPlaceId: string) {
    // Picked alt cleared but stop stays removed (user can re-pick).
    setChanges((prev) => {
      const next = new Map(prev);
      next.set(originalPlaceId, { kind: "remove" });
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
        <ol className="flex flex-col gap-0 pb-24">
          {data.stops.map((s, idx) => {
            const c = changes.get(s.place_id);
            const isRemoved = c !== undefined;
            const showLeg = !isRemoved && s.travel_minutes_from_prev != null;
            const selectedAlt = c?.kind === "swap" ? c.with : null;
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
                <StopCard
                  stop={s}
                  change={c}
                  onRemove={() => markRemove(s.place_id)}
                  onRestore={() => restoreOriginal(s.place_id)}
                />
                {isRemoved && (
                  <div className="ml-6 mt-1 mb-3">
                    {altsQuery.isLoading && (
                      <div className="text-xs text-ink/40">Finding nearby alternatives…</div>
                    )}
                    {altsQuery.data && (
                      <AlternativesPicker
                        alternatives={altsQuery.data}
                        selected={selectedAlt}
                        usedElsewhere={
                          new Set(
                            Array.from(swappedAltIds).filter(
                              (pid) => pid !== selectedAlt?.place_id,
                            ),
                          )
                        }
                        onPick={(alt) => pickAlternative(s.place_id, alt)}
                        onClear={() => clearAlternative(s.place_id)}
                      />
                    )}
                  </div>
                )}
              </li>
            );
          })}
        </ol>
        <ItineraryMap stops={visibleStops} routeGeometry={data.route_geometry} />
      </div>

      {changes.size > 0 && (
        <div className="fixed inset-x-0 bottom-0 z-40 border-t border-ink/10 bg-white/95 px-6 py-3 shadow-lg backdrop-blur">
          <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3">
            <div className="text-sm text-ink/70">
              {removeCount > 0 && (
                <>
                  <span className="font-medium text-ink">{removeCount}</span> removed
                </>
              )}
              {removeCount > 0 && swapCount > 0 && " · "}
              {swapCount > 0 && (
                <>
                  <span className="font-medium text-ink">{swapCount}</span> swapped
                </>
              )}
              {" · "}
              {finalPlaceIds.length} final stop{finalPlaceIds.length === 1 ? "" : "s"}
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setChanges(new Map())}
                className="rounded-md border border-ink/15 px-3 py-1.5 text-sm hover:bg-ink/5"
              >
                Reset
              </button>
              <button
                type="button"
                disabled={!canApply || recompute.isPending}
                onClick={() => recompute.mutate(finalPlaceIds)}
                className="rounded-md bg-accent px-4 py-1.5 text-sm font-medium text-white shadow-sm hover:bg-accent-dark disabled:opacity-50"
              >
                {recompute.isPending
                  ? "Recalculating…"
                  : finalPlaceIds.length < 2
                  ? "Keep at least 2 stops"
                  : "Apply changes"}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
