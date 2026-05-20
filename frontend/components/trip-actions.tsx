"use client";

import { useState } from "react";
import type { Itinerary } from "@/lib/api";

/**
 * Build a Google Maps Directions URL that opens the full multi-stop route in
 * the user's Google Maps app or browser. Format docs:
 *   https://developers.google.com/maps/documentation/urls/get-started#directions-action
 */
function googleMapsRouteUrl(itin: Itinerary): string | null {
  const points = itin.stops.filter((s) => s.latitude != null && s.longitude != null);
  if (points.length < 2) return null;
  const params = new URLSearchParams({
    api: "1",
    origin: `${points[0].latitude},${points[0].longitude}`,
    destination: `${points.at(-1)!.latitude},${points.at(-1)!.longitude}`,
    travelmode: itin.transit_mode,
  });
  const waypoints = points
    .slice(1, -1)
    .map((p) => `${p.latitude},${p.longitude}`)
    .join("|");
  if (waypoints) params.set("waypoints", waypoints);
  return `https://www.google.com/maps/dir/?${params.toString()}`;
}

function appleMapsRouteUrl(itin: Itinerary): string | null {
  const points = itin.stops.filter((s) => s.latitude != null && s.longitude != null);
  if (points.length < 2) return null;
  // Apple Maps supports up to one daddr with intermediates via '+to:'
  const head = `${points[0].latitude},${points[0].longitude}`;
  const rest = points
    .slice(1)
    .map((p) => `${p.latitude},${p.longitude}`)
    .join("+to:");
  const dirflg = itin.transit_mode === "walking" ? "w" : itin.transit_mode === "transit" ? "r" : "d";
  return `https://maps.apple.com/?saddr=${head}&daddr=${rest}&dirflg=${dirflg}`;
}

export function TripActions({ itinerary }: { itinerary: Itinerary }) {
  const [copied, setCopied] = useState(false);
  const gmaps = googleMapsRouteUrl(itinerary);
  const amaps = appleMapsRouteUrl(itinerary);

  const shareUrl =
    typeof window !== "undefined" && itinerary.share_token
      ? `${window.location.origin}/share/${itinerary.share_token}`
      : null;

  async function copyShare() {
    if (!shareUrl) return;
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      window.prompt("Copy this link:", shareUrl);
    }
  }

  return (
    <div className="mt-4 flex flex-wrap gap-2">
      {shareUrl && (
        <button
          type="button"
          onClick={copyShare}
          className="inline-flex items-center gap-1.5 rounded-md border border-ink/15 bg-white px-3 py-1.5 text-sm hover:bg-ink/5"
        >
          <span aria-hidden>{copied ? "✓" : "🔗"}</span>
          {copied ? "Copied!" : "Copy share link"}
        </button>
      )}
      {gmaps && (
        <a
          href={gmaps}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1.5 rounded-md border border-ink/15 bg-white px-3 py-1.5 text-sm hover:bg-ink/5"
        >
          <span aria-hidden>🗺️</span>
          Open in Google Maps
        </a>
      )}
      {amaps && (
        <a
          href={amaps}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1.5 rounded-md border border-ink/15 bg-white px-3 py-1.5 text-sm hover:bg-ink/5"
        >
          <span aria-hidden>🍎</span>
          Open in Apple Maps
        </a>
      )}
    </div>
  );
}
