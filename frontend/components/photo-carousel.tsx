"use client";

import { useRef, useState } from "react";

/**
 * Lightweight horizontal photo carousel for stop cards. Scroll-snap on
 * touch; prev/next chevrons appear on hover at desktop sizes. Each photo
 * is fetched lazily via /api/places/{id}/photo?idx=N.
 */
export function PhotoCarousel({
  basePath,
  count,
  className = "",
}: {
  basePath: string; // e.g. "/api/places/CHIJ.../photo"
  count: number;
  className?: string;
}) {
  const scrollerRef = useRef<HTMLDivElement | null>(null);
  const [active, setActive] = useState(0);

  if (count <= 0) return null;

  function go(delta: number) {
    const sc = scrollerRef.current;
    if (!sc) return;
    const slideWidth = sc.clientWidth;
    sc.scrollBy({ left: delta * slideWidth, behavior: "smooth" });
  }

  function onScroll() {
    const sc = scrollerRef.current;
    if (!sc) return;
    const idx = Math.round(sc.scrollLeft / sc.clientWidth);
    if (idx !== active) setActive(Math.min(count - 1, Math.max(0, idx)));
  }

  return (
    <div className={`group relative ${className}`}>
      <div
        ref={scrollerRef}
        onScroll={onScroll}
        className="flex h-32 w-full snap-x snap-mandatory overflow-x-auto scroll-smooth"
        style={{ scrollbarWidth: "none" }}
      >
        {Array.from({ length: count }).map((_, i) => (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            key={i}
            src={`${basePath}?idx=${i}`}
            alt=""
            loading={i === 0 ? "eager" : "lazy"}
            className="h-32 w-full flex-shrink-0 snap-center object-cover"
            onError={(e) => {
              (e.currentTarget as HTMLImageElement).style.display = "none";
            }}
          />
        ))}
      </div>
      {count > 1 && (
        <>
          <button
            type="button"
            onClick={() => go(-1)}
            disabled={active === 0}
            aria-label="Previous photo"
            className="absolute left-1.5 top-1/2 hidden h-7 w-7 -translate-y-1/2 items-center justify-center rounded-full bg-white/85 text-ink shadow transition group-hover:flex disabled:opacity-40"
          >
            ‹
          </button>
          <button
            type="button"
            onClick={() => go(1)}
            disabled={active === count - 1}
            aria-label="Next photo"
            className="absolute right-1.5 top-1/2 hidden h-7 w-7 -translate-y-1/2 items-center justify-center rounded-full bg-white/85 text-ink shadow transition group-hover:flex disabled:opacity-40"
          >
            ›
          </button>
          <div className="absolute bottom-1.5 left-1/2 flex -translate-x-1/2 gap-1">
            {Array.from({ length: count }).map((_, i) => (
              <span
                key={i}
                className={`h-1.5 w-1.5 rounded-full transition ${
                  i === active ? "bg-white" : "bg-white/50"
                }`}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
