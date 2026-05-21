"use client";

import type { Itinerary } from "@/lib/api";

type Mode = Itinerary["transit_mode"];

function WalkIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden className="h-6 w-6">
      <circle cx="13" cy="4" r="2" />
      <path d="M14.12 10.4 12 12l1.7 1.5L11 20h2.3l1.95-5.2 2.05 1.7v5h2v-6.5l-2.1-1.7.6-3c1.3 1.5 3.3 2.5 5.5 2.5v-2c-1.9 0-3.5-1-4.3-2.4l-1-1.6c-.4-.6-1-1-1.7-1-.3 0-.5.1-.8.1L11 7.85V12h2v-2.7l1.12-.9zM7.8 10.6 7 14H4l-.5-1.3 4.3-2.1z" />
    </svg>
  );
}

function DriveIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden className="h-6 w-6">
      <path d="M18.92 6.01C18.72 5.42 18.16 5 17.5 5h-11c-.66 0-1.21.42-1.42 1.01L3 12v8a1 1 0 0 0 1 1h1a1 1 0 0 0 1-1v-1h12v1a1 1 0 0 0 1 1h1a1 1 0 0 0 1-1v-8l-2.08-5.99zM6.5 16a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3zm11 0a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3zM5 11l1.5-4.5h11L19 11H5z" />
    </svg>
  );
}

function BikeIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden className="h-6 w-6">
      <path d="M5 20.5A3.5 3.5 0 0 1 1.5 17a3.5 3.5 0 0 1 3.5-3.5A3.5 3.5 0 0 1 8.5 17 3.5 3.5 0 0 1 5 20.5zm0-5.6a2.1 2.1 0 1 0 0 4.2 2.1 2.1 0 0 0 0-4.2zm10 .6c0-.83-.16-1.62-.45-2.34l.71-.71c.45.93.74 1.95.74 3.05A4.5 4.5 0 0 1 11.5 20a4.5 4.5 0 0 1-4.5-4.5h1.4a3.1 3.1 0 0 0 6.2 0zm-6.6 0H6L8.5 10l2.5 3v5h-1.4v-3.1L8 13.5 6.4 15.5zM18 4.5l-2.5 5L13 7l2.5-4 2.5 1.5zM19 20.5a3.5 3.5 0 0 1-3.5-3.5 3.5 3.5 0 0 1 3.5-3.5 3.5 3.5 0 0 1 3.5 3.5 3.5 3.5 0 0 1-3.5 3.5zm0-5.6a2.1 2.1 0 1 0 0 4.2 2.1 2.1 0 0 0 0-4.2z" />
    </svg>
  );
}

function TransitIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden className="h-6 w-6">
      <path d="M12 2c-4 0-8 .5-8 4v9.5A3.5 3.5 0 0 0 7.5 19L6 20.5v.5h12v-.5L16.5 19A3.5 3.5 0 0 0 20 15.5V6c0-3.5-4-4-8-4zM7.5 17a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3zm3.5-7H6V6h5v4zm2 0V6h5v4h-5zm3.5 7a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3z" />
    </svg>
  );
}

const OPTIONS: { mode: Mode; label: string; Icon: () => React.JSX.Element }[] = [
  { mode: "walking", label: "Walking", Icon: WalkIcon },
  { mode: "bicycling", label: "Biking", Icon: BikeIcon },
  { mode: "driving", label: "Driving", Icon: DriveIcon },
  { mode: "transit", label: "Transit", Icon: TransitIcon },
];

export function TransitModePicker({
  value,
  onChange,
}: {
  value: Mode;
  onChange: (m: Mode) => void;
}) {
  return (
    <div
      role="radiogroup"
      aria-label="Transit mode"
      className="flex overflow-hidden rounded-md border border-ink/15 bg-white"
    >
      {OPTIONS.map(({ mode, label, Icon }, i) => {
        const active = value === mode;
        return (
          <button
            key={mode}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => onChange(mode)}
            title={label}
            className={`flex flex-1 flex-col items-center gap-1 px-2 py-2.5 text-xs font-medium transition ${
              i > 0 ? "border-l border-ink/10" : ""
            } ${
              active
                ? "bg-accent text-white"
                : "text-ink/60 hover:bg-ink/5 hover:text-ink"
            }`}
          >
            <Icon />
            <span>{label}</span>
          </button>
        );
      })}
    </div>
  );
}
