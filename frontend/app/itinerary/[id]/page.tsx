"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Image from "next/image";
import Link from "next/link";
import { use, useState } from "react";
import {
  api,
  computeSchedule,
  dwellMinutes,
  evaluateOpenAt,
  formatClock,
  formatDistance,
  formatMinutes,
  photoSrc,
  type Alternative,
  type Itinerary,
  type ScheduledStop,
  type Stop,
  type TravelStep,
} from "@/lib/api";
import { AISparkleIcon } from "@/components/ai-sparkle";
import { ItineraryMap } from "@/components/itinerary-map";
import { LoadingScreen } from "@/components/loading-screen";
import { NearbyRestaurants } from "@/components/nearby-restaurants";
import { TripActions } from "@/components/trip-actions";
import { HourChip, WeatherBanner, useWeather } from "@/components/weather-banner";

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
  itineraryId,
  schedule,
  hourWeather,
  onRemove,
  busy,
  canRemove,
  isEndpoint,
}: {
  stop: Stop;
  itineraryId: number;
  schedule: ScheduledStop | null;
  hourWeather: import("@/lib/api").WeatherHour | null;
  onRemove: () => void;
  busy: boolean;
  canRemove: boolean;
  isEndpoint: boolean;
}) {
  const img = photoSrc(stop.photo_url);
  return (
    <div className="relative overflow-hidden rounded-lg border border-ink/10 bg-white shadow-sm">
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
      <div className="relative p-3 pr-10">
        <button
          type="button"
          onClick={onRemove}
          disabled={busy || !canRemove}
          aria-label="Remove stop"
          title={canRemove ? "Remove stop" : "Need at least 2 stops"}
          className="absolute right-2 top-2 z-10 flex h-6 w-6 items-center justify-center rounded-full bg-ink/5 text-sm font-semibold text-ink/40 transition hover:bg-red-100 hover:text-red-700 disabled:cursor-not-allowed disabled:opacity-40"
        >
          ×
        </button>
        <div className="flex flex-wrap items-baseline justify-between gap-x-2 gap-y-1">
          <div className="text-xs text-ink/50">Stop {stop.position + 1}</div>
          {schedule && (
            <div className="flex items-center gap-1.5 text-xs tabular-nums text-ink/60">
              <span>
                {formatClock(schedule.arrival)} – {formatClock(schedule.depart)}
              </span>
              {hourWeather && <HourChip hour={hourWeather} />}
            </div>
          )}
        </div>
        <div className="font-medium">{stop.name}</div>
        <div className="flex items-center gap-2 text-sm text-ink/60">
          {stop.rating != null && <span>★ {stop.rating.toFixed(1)}</span>}
          {schedule && (
            <span className="text-ink/40">· ~{dwellMinutes(stop.name)} min here</span>
          )}
        </div>
        {schedule && stop.opening_hours && (() => {
          const arr = evaluateOpenAt(stop.opening_hours, schedule.arrival);
          const dep = evaluateOpenAt(stop.opening_hours, schedule.depart);
          if (arr.open && dep.open) {
            const closes = arr.closesAt ?? dep.closesAt;
            return closes ? (
              <div className="mt-1 text-xs text-emerald-700">
                Open until {formatClock(closes)}
              </div>
            ) : (
              <div className="mt-1 text-xs text-emerald-700">Open all day</div>
            );
          }
          if (!arr.open && !dep.open) {
            return (
              <div className="mt-1 inline-flex items-center gap-1 rounded-md bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800">
                Closed during this window
                {arr.opensAt && <> · opens {formatClock(arr.opensAt)}</>}
              </div>
            );
          }
          // Mixed (open at arrival but closes mid-visit, or opens mid-visit).
          return (
            <div className="mt-1 inline-flex items-center gap-1 rounded-md bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-900">
              Closes during your visit
              {arr.closesAt && <> at {formatClock(arr.closesAt)}</>}
            </div>
          );
        })()}
        {stop.description && !isEndpoint && (
          <p className="mt-2 text-sm leading-snug text-ink/75">{stop.description}</p>
        )}
        <a
          href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(stop.name)}&query_place_id=${stop.place_id}`}
          target="_blank"
          rel="noreferrer"
          className="mt-2 inline-block text-xs text-ink/50 hover:text-accent-dark hover:underline"
        >
          View on Google Maps →
        </a>
        <NearbyRestaurants itineraryId={itineraryId} placeId={stop.place_id} />
      </div>
    </div>
  );
}

function AlternativeCard({
  alt,
  onAdd,
  busy,
  canAdd,
}: {
  alt: Alternative;
  onAdd: () => void;
  busy: boolean;
  canAdd: boolean;
}) {
  const img = photoSrc(alt.photo_url);
  return (
    <div className="flex flex-col overflow-hidden rounded-lg border border-ink/10 bg-white shadow-sm transition hover:border-accent/40 hover:shadow">
      {img ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={img}
          alt=""
          loading="lazy"
          className="h-24 w-full object-cover"
          onError={(e) => {
            (e.currentTarget as HTMLImageElement).style.display = "none";
          }}
        />
      ) : (
        <div className="h-24 w-full bg-ink/5" />
      )}
      <div className="flex flex-1 flex-col p-3">
        <div className="text-xs text-ink/50">Suggestion</div>
        <div className="font-medium leading-tight">{alt.name}</div>
        {alt.rating != null && (
          <div className="mt-0.5 text-sm text-ink/60">★ {alt.rating.toFixed(1)}</div>
        )}
        <button
          type="button"
          onClick={onAdd}
          disabled={busy || !canAdd}
          className="mt-3 inline-flex items-center justify-center gap-1.5 rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-white shadow-sm transition hover:bg-accent-dark disabled:cursor-not-allowed disabled:opacity-50"
          title={canAdd ? "Add to trip" : "Maximum stops reached"}
        >
          <span aria-hidden>＋</span> Add to trip
        </button>
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

  const altsQuery = useQuery<Alternative[]>({
    queryKey: ["itinerary-alternatives", id],
    queryFn: () => api.get(`/itineraries/${id}/alternatives?limit=12`),
    enabled: !!data,
    staleTime: 5 * 60 * 1000,
  });

  const [startTime, setStartTime] = useState("09:00");
  const [tripDate, setTripDate] = useState(() => new Date().toISOString().slice(0, 10));

  // Weather centered on the first stop with coords.
  const firstWithCoords = data?.stops.find(
    (s) => s.latitude != null && s.longitude != null,
  );
  const weatherQuery = useWeather(
    firstWithCoords?.latitude,
    firstWithCoords?.longitude,
    tripDate,
  );
  const weather = weatherQuery.data ?? null;

  const recompute = useMutation({
    mutationFn: (placeIds: string[]) =>
      api.post<Itinerary>(`/itineraries/${id}/recompute`, { kept_place_ids: placeIds }),
    onSuccess: (updated) => {
      qc.setQueryData(["itinerary", id], updated);
      // Alternatives will be different now (different already-used set).
      qc.invalidateQueries({ queryKey: ["itinerary-alternatives", id] });
    },
  });

  const summarize = useMutation({
    mutationFn: () => api.post<{ summary: string }>(`/itineraries/${id}/summarize`, {}),
    onSuccess: ({ summary }) => {
      const existing = qc.getQueryData<Itinerary>(["itinerary", id]);
      if (existing) qc.setQueryData(["itinerary", id], { ...existing, summary });
    },
  });

  if (isLoading) return <LoadingScreen />;
  if (error || !data) return <main className="p-8">Could not load itinerary.</main>;

  const verb = MODE_VERB[data.transit_mode];
  const tooLong = data.total_travel_minutes > TOO_LONG_MINUTES[data.transit_mode];

  const schedule = computeSchedule(data.stops, startTime);
  const endTime = schedule.length > 0 ? schedule[schedule.length - 1].depart : null;

  function removeStop(placeId: string) {
    if (!data || data.stops.length <= 2) return;
    const next = data.stops.filter((s) => s.place_id !== placeId).map((s) => s.place_id);
    recompute.mutate(next);
  }

  function addStop(altPlaceId: string) {
    if (!data || data.stops.length >= 10) return;
    const next = [...data.stops.map((s) => s.place_id), altPlaceId];
    recompute.mutate(next);
  }

  const canRemove = data.stops.length > 2;
  const canAdd = data.stops.length < 10;
  const busy = recompute.isPending;
  const usedIds = new Set(data.stops.map((s) => s.place_id));
  const visibleAlts = (altsQuery.data ?? []).filter((a) => !usedIds.has(a.place_id));

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <div className="mb-4 flex items-center justify-between gap-3">
        <Link
          href="/"
          aria-label="DayTour home"
          className="inline-flex items-center gap-2 text-ink/60 transition hover:text-ink"
        >
          <Image src="/daytour.png" alt="" width={28} height={28} />
          <span className="text-sm font-medium">DayTour</span>
        </Link>
        <TripActions itinerary={data} />
      </div>

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
        <div className="mt-4">
          {data.summary ? (
            <div className="rounded-lg border border-ink/10 bg-white px-4 py-3 text-[15px] leading-relaxed text-ink/90 shadow-sm">
              <div className="mb-1 inline-flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-ink/50">
                <AISparkleIcon className="h-3.5 w-3.5" />
                Your day, in brief
              </div>
              <div>{data.summary}</div>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => summarize.mutate()}
              disabled={summarize.isPending}
              className="group inline-flex items-center gap-2 rounded-full border border-ink/10 bg-white px-3.5 py-1.5 text-sm font-medium text-ink/80 shadow-sm transition hover:border-ink/20 hover:shadow disabled:opacity-60"
            >
              <AISparkleIcon className="h-4 w-4 transition group-hover:scale-110" />
              {summarize.isPending ? "Thinking…" : "Summarize my day"}
            </button>
          )}
          {summarize.isError && (
            <div className="mt-2 text-xs text-red-700">
              Couldn&apos;t generate a summary — try again in a moment.
            </div>
          )}
        </div>
        {tooLong && (
          <div className="mt-3 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">
            Heads up — that&apos;s a lot of {verb}ing for one day. Consider shrinking the
            radius, dropping stops, or switching transit mode.
          </div>
        )}
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <div className="flex flex-wrap items-center gap-3 rounded-lg border border-ink/10 bg-white px-3 py-2 text-sm">
            <label className="flex items-center gap-2">
              <span className="text-ink/60">On</span>
              <input
                type="date"
                value={tripDate}
                onChange={(e) => setTripDate(e.target.value)}
                className="rounded border border-ink/15 bg-white px-2 py-1 tabular-nums"
              />
            </label>
            <label className="flex items-center gap-2">
              <span className="text-ink/60">starting at</span>
              <input
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className="rounded border border-ink/15 bg-white px-2 py-1 tabular-nums"
              />
            </label>
            {endTime && (
              <div className="text-ink/60">
                · Done by{" "}
                <span className="font-medium tabular-nums text-ink">{formatClock(endTime)}</span>
              </div>
            )}
          </div>
          {weather && <WeatherBanner weather={weather} />}
        </div>
      </header>

      <div className="grid gap-6 md:grid-cols-[1fr_2fr]">
        <ol className={`flex flex-col gap-0 ${busy ? "opacity-60" : ""}`}>
          {data.stops.map((s, idx) => (
            <li key={`${s.place_id}-${idx}`}>
              {s.travel_minutes_from_prev != null && (
                <div className="ml-4 flex flex-col gap-1 py-2">
                  <div className="flex items-center gap-2 text-xs text-ink/50">
                    <span className="h-4 w-px bg-ink/20" />
                    <span>↓ {formatMinutes(s.travel_minutes_from_prev)} {verb}</span>
                    {s.travel_meters_from_prev != null && (
                      <span className="text-ink/35">
                        · {formatDistance(s.travel_meters_from_prev)}
                      </span>
                    )}
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
                itineraryId={data.id}
                schedule={schedule[idx] ?? null}
                hourWeather={
                  weather && schedule[idx]
                    ? weather.hourly.find((h) => h.hour === schedule[idx].arrival.getHours()) ??
                      null
                    : null
                }
                busy={busy}
                canRemove={canRemove}
                isEndpoint={
                  idx === 0 || (!!data.end_loc && idx === data.stops.length - 1)
                }
                onRemove={() => removeStop(s.place_id)}
              />
            </li>
          ))}
        </ol>
        <div className="md:sticky md:top-6 md:self-start">
          <ItineraryMap
            stops={data.stops}
            routeGeometry={data.route_geometry}
            closeLoop={!data.end_loc}
          />
          {busy && (
            <div className="mt-2 text-center text-xs text-ink/50">
              Recalculating route…
            </div>
          )}
        </div>
      </div>

      {(altsQuery.isLoading || visibleAlts.length > 0) && (
        <section className="mt-10">
          <div className="mb-3 flex items-baseline justify-between">
            <h2 className="font-display text-xl text-ink">You might also like</h2>
            <span className="text-xs text-ink/50">
              Click <span aria-hidden>＋</span> to drop a place into your day —
              the route updates automatically.
            </span>
          </div>
          {altsQuery.isLoading ? (
            <div className="text-sm text-ink/40">Finding nearby places…</div>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
              {visibleAlts.map((alt) => (
                <AlternativeCard
                  key={alt.place_id}
                  alt={alt}
                  busy={busy}
                  canAdd={canAdd}
                  onAdd={() => addStop(alt.place_id)}
                />
              ))}
            </div>
          )}
          {!canAdd && (
            <div className="mt-2 text-xs text-ink/50">
              Already at the max of 10 stops. Remove one to add another.
            </div>
          )}
        </section>
      )}
    </main>
  );
}
