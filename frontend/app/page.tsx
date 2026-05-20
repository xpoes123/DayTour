"use client";

import { useQuery } from "@tanstack/react-query";
import Image from "next/image";
import Link from "next/link";
import { api, formatMinutes, photoSrc, type Itinerary } from "@/lib/api";

const FEATURED_SHARE_TOKEN = "xYWdodN2Fy8";

function FeaturedTrip() {
  const { data } = useQuery<Itinerary>({
    queryKey: ["featured", FEATURED_SHARE_TOKEN],
    queryFn: () => api.get(`/itineraries/by-share/${FEATURED_SHARE_TOKEN}`),
    staleTime: 60 * 60 * 1000,
  });
  if (!data) return null;
  return (
    <section className="mx-auto w-full max-w-4xl">
      <div className="mb-4 flex items-baseline justify-between">
        <div>
          <div className="text-[10px] font-semibold uppercase tracking-wider text-accent-dark">
            See an example
          </div>
          <h2 className="font-display text-xl text-ink/90">
            {data.title ?? `Day from ${data.start_loc}`}
          </h2>
          <p className="text-xs text-ink/55">
            {data.stops.length} stops · {data.transit_mode} ·{" "}
            {formatMinutes(data.total_travel_minutes)} on the move
          </p>
        </div>
        <Link
          href={`/share/${FEATURED_SHARE_TOKEN}`}
          className="text-sm font-medium text-accent-dark hover:underline"
        >
          View the full trip →
        </Link>
      </div>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        {data.stops.slice(0, 4).map((s, i) => {
          const img = photoSrc(s.photo_url);
          return (
            <Link
              key={s.place_id}
              href={`/share/${FEATURED_SHARE_TOKEN}`}
              className="group overflow-hidden rounded-lg border border-ink/10 bg-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
            >
              {img ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={img}
                  alt=""
                  loading="lazy"
                  className="h-24 w-full object-cover transition-transform group-hover:scale-105"
                  onError={(e) => {
                    (e.currentTarget as HTMLImageElement).style.display = "none";
                  }}
                />
              ) : (
                <div className="h-24 bg-ink/5" />
              )}
              <div className="p-2">
                <div className="text-[10px] uppercase tracking-wide text-ink/40">
                  Stop {i + 1}
                </div>
                <div className="truncate text-sm font-medium">{s.name}</div>
              </div>
            </Link>
          );
        })}
      </div>
    </section>
  );
}

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col items-center justify-center gap-12 px-6 py-16">
      <div className="flex flex-col items-center gap-6 text-center">
        <Image
          src="/daytour.png"
          alt="DayTour"
          width={160}
          height={160}
          priority
          className="drop-shadow-md"
        />
        <header>
          <h1 className="font-display text-5xl tracking-tight">DayTour</h1>
          <p className="mt-3 text-lg text-ink/70">
            Tell us where you are. We&apos;ll plot a day worth remembering.
          </p>
        </header>
        <div className="flex flex-col gap-3 sm:flex-row">
          <Link
            href="/plan"
            className="rounded-lg bg-accent px-6 py-3 font-medium text-white shadow-sm hover:bg-accent-dark"
          >
            Plan a day
          </Link>
          <Link
            href="/plan/prompt"
            className="rounded-lg border border-ink/20 px-6 py-3 font-medium text-ink hover:bg-ink hover:text-paper"
          >
            Describe my vibe →
          </Link>
        </div>
        <Link href="/auth" className="text-sm text-ink/50 hover:text-ink">
          Sign in or create an account
        </Link>
      </div>

      <FeaturedTrip />

      <section className="mx-auto grid w-full max-w-4xl gap-4 text-sm text-ink/70 sm:grid-cols-3">
        <div className="rounded-lg border border-ink/10 bg-white p-4">
          <div className="mb-1 text-xl">🗺</div>
          <div className="mb-1 font-medium text-ink">Real routes, real times</div>
          Streets-following polylines from OSRM, live bus & subway schedules from Google for
          transit.
        </div>
        <div className="rounded-lg border border-ink/10 bg-white p-4">
          <div className="mb-1 text-xl">✨</div>
          <div className="mb-1 font-medium text-ink">Curate without re-planning</div>
          Swap any stop for a nearby alternative; the route recomputes on the kept subset.
        </div>
        <div className="rounded-lg border border-ink/10 bg-white p-4">
          <div className="mb-1 text-xl">🤖</div>
          <div className="mb-1 font-medium text-ink">AI does the boring parts</div>
          Type a vibe, get a plan. Every stop gets a one-sentence preview that says what&apos;s
          actually there.
        </div>
      </section>
    </main>
  );
}
