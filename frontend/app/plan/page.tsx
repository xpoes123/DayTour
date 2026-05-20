"use client";

import Image from "next/image";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, type Itinerary } from "@/lib/api";
import { PlaceAutocomplete } from "@/components/place-autocomplete";

export default function PlanPage() {
  const router = useRouter();

  const [startLoc, setStartLoc] = useState("");
  const [radiusM, setRadiusM] = useState(4000);
  const [stopCount, setStopCount] = useState(5);
  const [transitMode, setTransitMode] = useState<
    "walking" | "driving" | "bicycling" | "transit"
  >("walking");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const itin = await api.post<Itinerary>("/itineraries", {
        start_loc: startLoc,
        radius_m: radiusM,
        stop_count: stopCount,
        transit_mode: transitMode,
      });
      router.push(`/itinerary/${itin.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="mx-auto max-w-xl px-6 py-12">
      <header className="mb-8 flex items-center gap-4">
        <Image src="/daytour.png" alt="" width={56} height={56} />
        <div>
          <h1 className="font-display text-3xl tracking-tight">Plan a day</h1>
          <p className="text-sm text-ink/60">
            Pick a starting point and we&apos;ll string together stops.
          </p>
        </div>
      </header>

      <form onSubmit={onSubmit} className="flex flex-col gap-5">
        <label className="flex flex-col gap-1.5">
          <span className="text-sm font-medium text-ink/80">Starting location</span>
          <PlaceAutocomplete
            value={startLoc}
            onChange={setStartLoc}
            placeholder="Wisconsin State Capitol"
            required
          />
        </label>

        <label className="flex flex-col gap-1.5">
          <span className="text-sm font-medium text-ink/80">
            Radius:{" "}
            <span className="tabular-nums">{radiusM.toLocaleString()} m</span>
            <span className="ml-1 text-ink/50">
              · <span className="tabular-nums">{(radiusM / 1609.344).toFixed(2)} mi</span>
            </span>
          </span>
          <input
            type="range"
            min={500}
            max={20000}
            step={500}
            value={radiusM}
            onChange={(e) => setRadiusM(Number(e.target.value))}
            className="accent-accent"
          />
        </label>

        <label className="flex flex-col gap-1.5">
          <span className="text-sm font-medium text-ink/80">
            Stops: <span className="tabular-nums">{stopCount}</span>
          </span>
          <input
            type="range"
            min={2}
            max={10}
            value={stopCount}
            onChange={(e) => setStopCount(Number(e.target.value))}
            className="accent-accent"
          />
        </label>

        <label className="flex flex-col gap-1.5">
          <span className="text-sm font-medium text-ink/80">Transit</span>
          <select
            value={transitMode}
            onChange={(e) => setTransitMode(e.target.value as typeof transitMode)}
            className="field"
          >
            <option value="walking">Walking</option>
            <option value="driving">Driving</option>
            <option value="bicycling">Biking</option>
            <option value="transit">Transit</option>
          </select>
        </label>

        {error && (
          <div className="rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-900">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="rounded-md bg-accent px-4 py-2.5 font-medium text-white shadow-sm hover:bg-accent-dark disabled:opacity-50"
        >
          {submitting ? "Planning…" : "Build my day"}
        </button>
      </form>
    </main>
  );
}
