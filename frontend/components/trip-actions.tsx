"use client";

import { useEffect, useRef, useState } from "react";
import type { Itinerary } from "@/lib/api";

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
  const head = `${points[0].latitude},${points[0].longitude}`;
  const rest = points
    .slice(1)
    .map((p) => `${p.latitude},${p.longitude}`)
    .join("+to:");
  const dirflg =
    itin.transit_mode === "walking" ? "w" : itin.transit_mode === "transit" ? "r" : "d";
  return `https://maps.apple.com/?saddr=${head}&daddr=${rest}&dirflg=${dirflg}`;
}

function ShareIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden className="h-4 w-4">
      <path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92S21 19.61 21 18s-1.34-3-3-3z" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden className="h-4 w-4">
      <path d="M9 16.17 4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
    </svg>
  );
}

function LinkIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden className="h-5 w-5">
      <path d="M3.9 12c0-1.71 1.39-3.1 3.1-3.1h4V7H7c-2.76 0-5 2.24-5 5s2.24 5 5 5h4v-1.9H7c-1.71 0-3.1-1.39-3.1-3.1zM8 13h8v-2H8v2zm9-6h-4v1.9h4c1.71 0 3.1 1.39 3.1 3.1s-1.39 3.1-3.1 3.1h-4V17h4c2.76 0 5-2.24 5-5s-2.24-5-5-5z" />
    </svg>
  );
}

function MapPinIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden className="h-5 w-5">
      <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
    </svg>
  );
}

function AppleIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden className="h-5 w-5">
      <path d="M17.05 12.04c-.03-2.94 2.4-4.36 2.51-4.43-1.37-2-3.5-2.27-4.26-2.31-1.81-.18-3.54 1.07-4.46 1.07-.94 0-2.34-1.04-3.86-1.01-1.98.03-3.83 1.16-4.85 2.93-2.08 3.6-.53 8.9 1.5 11.81.99 1.43 2.16 3.03 3.7 2.97 1.5-.06 2.06-.96 3.86-.96 1.8 0 2.31.96 3.88.93 1.61-.03 2.62-1.45 3.59-2.89 1.14-1.65 1.61-3.26 1.63-3.34-.04-.02-3.13-1.2-3.24-4.77zM14.4 4.18c.82-1 1.38-2.4 1.23-3.78-1.18.05-2.62.79-3.47 1.79-.76.88-1.43 2.3-1.25 3.66 1.32.1 2.66-.67 3.49-1.67z" />
    </svg>
  );
}

export function TripActions({ itinerary }: { itinerary: Itinerary }) {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const wrapRef = useRef<HTMLDivElement | null>(null);

  const gmaps = googleMapsRouteUrl(itinerary);
  const amaps = appleMapsRouteUrl(itinerary);
  const shareUrl =
    typeof window !== "undefined" && itinerary.share_token
      ? `${window.location.origin}/share/${itinerary.share_token}`
      : null;

  useEffect(() => {
    if (!open) return;
    function onDown(e: MouseEvent) {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

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
    <div ref={wrapRef} className="relative inline-block">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
        className="inline-flex items-center gap-1.5 rounded-md border border-ink/15 bg-white px-3 py-1.5 text-sm font-medium text-ink/80 shadow-sm hover:bg-ink/5"
      >
        <ShareIcon />
        Share
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 z-30 mt-2 w-64 overflow-hidden rounded-lg border border-ink/10 bg-white shadow-lg ring-1 ring-ink/5"
        >
          {shareUrl && (
            <button
              type="button"
              role="menuitem"
              onClick={copyShare}
              className="flex w-full items-center gap-3 px-3 py-2.5 text-left text-sm transition hover:bg-ink/5"
            >
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-accent/15 text-accent-dark">
                {copied ? <CheckIcon /> : <LinkIcon />}
              </span>
              <div className="flex flex-col">
                <span className="font-medium text-ink">
                  {copied ? "Link copied!" : "Copy share link"}
                </span>
                <span className="truncate text-xs text-ink/50">
                  {shareUrl.replace(/^https?:\/\//, "")}
                </span>
              </div>
            </button>
          )}
          {gmaps && (
            <a
              href={gmaps}
              target="_blank"
              rel="noreferrer"
              role="menuitem"
              onClick={() => setOpen(false)}
              className="flex w-full items-center gap-3 border-t border-ink/5 px-3 py-2.5 text-left text-sm transition hover:bg-ink/5"
            >
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-amber-100 text-amber-800">
                <MapPinIcon />
              </span>
              <div className="flex flex-col">
                <span className="font-medium text-ink">Open in Google Maps</span>
                <span className="text-xs text-ink/50">Route with all stops</span>
              </div>
            </a>
          )}
          {amaps && (
            <a
              href={amaps}
              target="_blank"
              rel="noreferrer"
              role="menuitem"
              onClick={() => setOpen(false)}
              className="flex w-full items-center gap-3 border-t border-ink/5 px-3 py-2.5 text-left text-sm transition hover:bg-ink/5"
            >
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-ink/10 text-ink/80">
                <AppleIcon />
              </span>
              <div className="flex flex-col">
                <span className="font-medium text-ink">Open in Apple Maps</span>
                <span className="text-xs text-ink/50">Route with all stops</span>
              </div>
            </a>
          )}
        </div>
      )}
    </div>
  );
}
