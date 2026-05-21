"use client";

import { useQuery } from "@tanstack/react-query";
import Image from "next/image";
import Link from "next/link";
import { use, useState } from "react";
import {
  api,
  computeSchedule,
  dwellMinutes,
  formatClock,
  formatDistance,
  formatMinutes,
  photoSrc,
  type Itinerary,
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

const STEP_STYLE: Record<TravelStep["mode"], { bg: string; label: string; icon: string }> = {
  walk: { bg: "bg-ink/10 text-ink/70", label: "Walk", icon: "🚶" },
  bus: { bg: "bg-amber-100 text-amber-900", label: "Bus", icon: "🚌" },
  subway: { bg: "bg-accent/20 text-accent-dark", label: "Subway", icon: "🚇" },
  rail: { bg: "bg-emerald-100 text-emerald-900", label: "Rail", icon: "🚆" },
};

export default function SharedItineraryPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = use(params);
  const [startTime, setStartTime] = useState("09:00");
  const [tripDate, setTripDate] = useState(() => new Date().toISOString().slice(0, 10));
  const { data, isLoading, error } = useQuery<Itinerary>({
    queryKey: ["share", token],
    queryFn: () => api.get(`/itineraries/by-share/${token}`),
  });

  // Hooks above any conditional return — weather query must always be called.
  const firstWithCoords = data?.stops.find(
    (s) => s.latitude != null && s.longitude != null,
  );
  const { data: weather } = useWeather(
    firstWithCoords?.latitude,
    firstWithCoords?.longitude,
    tripDate,
  );

  if (isLoading) return <LoadingScreen message="Loading this trip…" />;
  if (error || !data)
    return (
      <main className="mx-auto max-w-xl p-8">
        <h1 className="font-display text-2xl">This trip is no longer available</h1>
        <p className="mt-2 text-ink/60">
          The share link is invalid or the itinerary has been deleted.
        </p>
        <Link
          href="/"
          className="mt-4 inline-block rounded-md bg-accent px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-accent-dark"
        >
          Plan your own day →
        </Link>
      </main>
    );

  const verb = MODE_VERB[data.transit_mode];
  const schedule = computeSchedule(data.stops, startTime);
  const endTime = schedule.length > 0 ? schedule[schedule.length - 1].depart : null;

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
      <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-accent-dark">
        Shared trip
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
        {data.summary && (
          <div className="mt-4 rounded-lg border border-ink/10 bg-white px-4 py-3 text-[15px] leading-relaxed text-ink/90 shadow-sm">
            <div className="mb-1 inline-flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-ink/50">
              <AISparkleIcon className="h-3.5 w-3.5" />
              Your day, in brief
            </div>
            <div>{data.summary}</div>
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
        <ol className="flex flex-col gap-0">
          {data.stops.map((s, idx) => {
            const img = photoSrc(s.photo_url);
            const sched = schedule[idx];
            return (
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
                        {s.travel_steps_from_prev.map((st, i) => {
                          const style = STEP_STYLE[st.mode];
                          const mins = Math.max(1, Math.round(st.duration_sec / 60));
                          return (
                            <span
                              key={i}
                              className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${style.bg}`}
                            >
                              <span aria-hidden>{style.icon}</span>
                              <span>{st.label ?? style.label}</span>
                              <span className="opacity-70">·</span>
                              <span className="tabular-nums">{mins}m</span>
                            </span>
                          );
                        })}
                      </div>
                    )}
                  </div>
                )}
                <div className="overflow-hidden rounded-lg border border-ink/10 bg-white shadow-sm">
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
                  <div className="p-3">
                    <div className="flex items-baseline justify-between gap-2">
                      <div className="text-xs text-ink/50">Stop {s.position + 1}</div>
                      {sched && (
                        <div className="flex items-center gap-1.5 text-xs tabular-nums text-ink/60">
                          <span>
                            {formatClock(sched.arrival)} – {formatClock(sched.depart)}
                          </span>
                          {(() => {
                            const h =
                              weather?.hourly.find(
                                (hh) => hh.hour === sched.arrival.getHours(),
                              ) ?? null;
                            return h ? <HourChip hour={h} /> : null;
                          })()}
                        </div>
                      )}
                    </div>
                    <div className="font-medium">{s.name}</div>
                    <div className="flex items-center gap-2 text-sm text-ink/60">
                      {s.rating != null && <span>★ {s.rating.toFixed(1)}</span>}
                      {sched && (
                        <span className="text-ink/40">
                          · ~{dwellMinutes(s.name)} min here
                        </span>
                      )}
                    </div>
                    {s.description && (
                      <p className="mt-2 text-sm leading-snug text-ink/75">{s.description}</p>
                    )}
                    <a
                      href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(s.name)}&query_place_id=${s.place_id}`}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-2 inline-block text-xs text-ink/50 hover:text-accent-dark hover:underline"
                    >
                      View on Google Maps →
                    </a>
                    <NearbyRestaurants itineraryId={data.id} placeId={s.place_id} />
                  </div>
                </div>
              </li>
            );
          })}
        </ol>
        <div className="md:sticky md:top-6 md:self-start">
          <ItineraryMap stops={data.stops} routeGeometry={data.route_geometry} />
        </div>
      </div>

      <div className="mt-8 rounded-lg border border-ink/10 bg-paper p-4 text-sm text-ink/70">
        Like what you see?{" "}
        <Link href="/" className="font-medium text-accent-dark hover:underline">
          Plan your own day on DayTour →
        </Link>
      </div>
    </main>
  );
}
