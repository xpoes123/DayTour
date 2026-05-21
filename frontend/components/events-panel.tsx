"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, type EventItem, type Itinerary } from "@/lib/api";

function fmtEventTime(start_local: string): string {
  // start_local is either "YYYY-MM-DD" or "YYYY-MM-DDTHH:MM:SS"
  if (!start_local.includes("T")) return "All day";
  try {
    const [, time] = start_local.split("T");
    const [hh, mm] = time.split(":");
    const h = parseInt(hh, 10);
    const suffix = h >= 12 ? "PM" : "AM";
    const h12 = h === 0 ? 12 : h > 12 ? h - 12 : h;
    return `${h12}:${mm} ${suffix}`;
  } catch {
    return "";
  }
}

function EventCard({
  ev,
  busy,
  onAdd,
}: {
  ev: EventItem;
  busy: boolean;
  onAdd: () => void;
}) {
  return (
    <div className="flex flex-col overflow-hidden rounded-lg border border-ink/10 bg-white shadow-sm transition hover:border-accent/40 hover:shadow">
      {ev.image ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={ev.image}
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
      <div className="flex flex-1 flex-col gap-1 p-3">
        <div className="flex items-baseline justify-between gap-2">
          <div className="text-xs font-semibold uppercase tracking-wide text-accent-dark">
            {fmtEventTime(ev.start_local)}
          </div>
          {ev.genre && <div className="text-xs text-ink/45">{ev.genre}</div>}
        </div>
        <div className="font-medium leading-tight">{ev.name}</div>
        {ev.venue_name && (
          <div className="text-xs text-ink/55">{ev.venue_name}</div>
        )}
        <div className="mt-auto flex items-center justify-between gap-2 pt-2">
          {ev.url ? (
            <a
              href={ev.url}
              target="_blank"
              rel="noreferrer"
              className="text-xs text-ink/50 hover:text-accent-dark hover:underline"
            >
              Details →
            </a>
          ) : (
            <span />
          )}
          <button
            type="button"
            onClick={onAdd}
            disabled={busy}
            className="inline-flex items-center justify-center gap-1.5 rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-white shadow-sm transition hover:bg-accent-dark disabled:opacity-50"
          >
            <span aria-hidden>＋</span> Add to trip
          </button>
        </div>
      </div>
    </div>
  );
}

function CustomEventForm({
  itineraryId,
  tripDate,
  onAdded,
}: {
  itineraryId: number;
  tripDate: string;
  onAdded: (updated: Itinerary) => void;
}) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [venueQuery, setVenueQuery] = useState("");
  const [time, setTime] = useState("");
  const [error, setError] = useState<string | null>(null);

  const add = useMutation({
    mutationFn: () =>
      api.post<Itinerary>(`/itineraries/${itineraryId}/add-event`, {
        name: name.trim(),
        venue_query: venueQuery.trim(),
        start_local: time ? `${tripDate}T${time}` : undefined,
      }),
    onSuccess: (updated) => {
      onAdded(updated);
      setOpen(false);
      setName("");
      setVenueQuery("");
      setTime("");
      setError(null);
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : "Couldn't add that event");
    },
  });

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="inline-flex items-center gap-1.5 text-sm text-ink/60 hover:text-accent-dark"
      >
        <span aria-hidden>＋</span> Add a custom event
      </button>
    );
  }
  return (
    <div className="rounded-lg border border-ink/10 bg-white p-3 shadow-sm sm:w-96">
      <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink/55">
        Add a custom event
      </div>
      <div className="flex flex-col gap-2">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="What's the event? (free concert, farmer's market…)"
          className="field"
          maxLength={120}
        />
        <input
          value={venueQuery}
          onChange={(e) => setVenueQuery(e.target.value)}
          placeholder="Where? (venue or address — we'll geocode it)"
          className="field"
          maxLength={120}
        />
        <input
          type="time"
          value={time}
          onChange={(e) => setTime(e.target.value)}
          className="field tabular-nums"
        />
        {error && (
          <div className="rounded-md border border-red-300 bg-red-50 px-2 py-1.5 text-xs text-red-900">
            {error}
          </div>
        )}
        <div className="flex justify-end gap-2 text-xs">
          <button
            type="button"
            onClick={() => setOpen(false)}
            className="rounded px-2 py-1 text-ink/60 hover:bg-ink/5"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={add.isPending || !name.trim() || !venueQuery.trim()}
            onClick={() => add.mutate()}
            className="rounded bg-accent px-3 py-1 font-medium text-white shadow-sm hover:bg-accent-dark disabled:opacity-50"
          >
            {add.isPending ? "Adding…" : "Add event"}
          </button>
        </div>
      </div>
    </div>
  );
}

export function EventsPanel({
  itineraryId,
  lat,
  lon,
  date,
  tripDate,
}: {
  itineraryId: number;
  lat: number | null | undefined;
  lon: number | null | undefined;
  date: string;
  tripDate: string;
}) {
  const qc = useQueryClient();
  const { data: events } = useQuery<EventItem[]>({
    queryKey: ["events", lat, lon, date],
    enabled: lat != null && lon != null,
    staleTime: 20 * 60 * 1000,
    queryFn: () =>
      api.get<EventItem[]>(`/events?lat=${lat}&lon=${lon}&date=${date}`),
  });

  const add = useMutation({
    mutationFn: (ev: EventItem) =>
      api.post<Itinerary>(`/itineraries/${itineraryId}/add-event`, {
        external_id: `ticketmaster:${ev.id}`,
        name: ev.name,
        venue_name: ev.venue_name,
        venue_address: ev.venue_address,
        venue_lat: ev.venue_lat,
        venue_lon: ev.venue_lon,
        start_local: ev.start_local,
        url: ev.url,
      }),
    onSuccess: (updated) => {
      qc.setQueryData(["itinerary", itineraryId], updated);
    },
  });

  const hasTm = events && events.length > 0;
  // Always show the section so users can manually add events even when
  // Ticketmaster has nothing (or no key is configured).
  return (
    <section className="mt-10">
      <div className="mb-3 flex items-baseline justify-between">
        <h2 className="font-display text-xl text-ink">Events that day</h2>
        <CustomEventForm
          itineraryId={itineraryId}
          tripDate={tripDate}
          onAdded={(updated) => qc.setQueryData(["itinerary", itineraryId], updated)}
        />
      </div>
      {hasTm ? (
        <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
          {events!.map((ev) => (
            <EventCard
              key={ev.id}
              ev={ev}
              busy={add.isPending}
              onAdd={() => add.mutate(ev)}
            />
          ))}
        </div>
      ) : (
        <div className="rounded-lg border border-dashed border-ink/15 bg-ink/[0.02] p-4 text-sm text-ink/55">
          Nothing ticketed showing up for this date. Use{" "}
          <span className="font-medium text-ink/70">Add a custom event</span>{" "}
          above to drop in farmer&apos;s markets, free concerts, or anything else
          you know about.
        </div>
      )}
    </section>
  );
}
