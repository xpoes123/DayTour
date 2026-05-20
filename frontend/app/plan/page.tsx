"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function PlanPage() {
  const router = useRouter();
  const [startLoc, setStartLoc] = useState("");
  const [radiusM, setRadiusM] = useState(4000);
  const [stopCount, setStopCount] = useState(5);
  const [transitMode, setTransitMode] = useState<
    "walking" | "driving" | "bicycling" | "transit"
  >("walking");
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      const itin = await api.post("/itineraries", {
        start_loc: startLoc,
        radius_m: radiusM,
        stop_count: stopCount,
        transit_mode: transitMode,
      });
      router.push(`/itinerary/${itin.id}`);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="mx-auto max-w-xl px-6 py-12">
      <h1 className="font-display text-3xl">Plan a day</h1>
      <form onSubmit={onSubmit} className="mt-6 flex flex-col gap-4">
        <label className="flex flex-col gap-1">
          <span className="text-sm opacity-70">Starting location</span>
          <input
            value={startLoc}
            onChange={(e) => setStartLoc(e.target.value)}
            placeholder="Wisconsin State Capitol"
            className="rounded border px-3 py-2"
            required
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-sm opacity-70">Radius (meters): {radiusM}</span>
          <input
            type="range"
            min={500}
            max={20000}
            step={500}
            value={radiusM}
            onChange={(e) => setRadiusM(Number(e.target.value))}
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-sm opacity-70">Stops: {stopCount}</span>
          <input
            type="range"
            min={2}
            max={10}
            value={stopCount}
            onChange={(e) => setStopCount(Number(e.target.value))}
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-sm opacity-70">Transit</span>
          <select
            value={transitMode}
            onChange={(e) => setTransitMode(e.target.value as typeof transitMode)}
            className="rounded border px-3 py-2"
          >
            <option value="walking">Walking</option>
            <option value="driving">Driving</option>
            <option value="bicycling">Biking</option>
            <option value="transit">Transit</option>
          </select>
        </label>
        <button
          type="submit"
          disabled={submitting}
          className="rounded bg-ink px-4 py-2 text-paper disabled:opacity-50"
        >
          {submitting ? "Planning..." : "Build my day"}
        </button>
      </form>
    </main>
  );
}
