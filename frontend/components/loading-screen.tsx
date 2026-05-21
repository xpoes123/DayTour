"use client";

import Image from "next/image";

/**
 * On-brand full-viewport loading state. Centered logo gently floats with a
 * soft pulse ring expanding behind it; below, five dots light up in sequence
 * to evoke "plotting a route" stop by stop.
 */
export function LoadingScreen({ message = "Plotting your day…" }: { message?: string }) {
  return (
    <main className="flex min-h-[70vh] flex-col items-center justify-center gap-6 px-6">
      <div className="relative">
        <span
          aria-hidden
          className="absolute inset-0 -m-2 rounded-full bg-accent/30 animate-daytour-ping"
        />
        <div className="relative animate-daytour-float">
          <Image
            src="/daytour.png"
            alt="DayTour"
            width={96}
            height={96}
            priority
            className="drop-shadow-md"
          />
        </div>
      </div>
      <div className="text-sm font-medium text-ink/60">{message}</div>
      <div className="flex items-center gap-2" aria-hidden>
        {[0, 1, 2, 3, 4].map((i) => (
          <span
            key={i}
            className="h-2 w-2 rounded-full bg-accent animate-daytour-plot"
            style={{ animationDelay: `${i * 0.18}s` }}
          />
        ))}
      </div>
    </main>
  );
}
