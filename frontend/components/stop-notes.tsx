"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { api, type Itinerary } from "@/lib/api";

export function StopNotes({
  itineraryId,
  placeId,
  notes,
}: {
  itineraryId: number;
  placeId: string;
  notes: string | null;
}) {
  const qc = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(notes ?? "");
  const ta = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    setDraft(notes ?? "");
  }, [notes]);

  const save = useMutation({
    mutationFn: (text: string) =>
      api.patch<{ notes: string | null }>(
        `/itineraries/${itineraryId}/stops/${placeId}/notes`,
        { notes: text },
      ),
    onSuccess: ({ notes: saved }) => {
      // Patch the cached itinerary so the stop card shows the new note.
      const itin = qc.getQueryData<Itinerary>(["itinerary", itineraryId]);
      if (itin) {
        const next = {
          ...itin,
          stops: itin.stops.map((s) =>
            s.place_id === placeId ? { ...s, notes: saved } : s,
          ),
        };
        qc.setQueryData(["itinerary", itineraryId], next);
      }
      setEditing(false);
    },
  });

  if (!editing) {
    if (notes) {
      return (
        <button
          type="button"
          onClick={() => {
            setEditing(true);
            queueMicrotask(() => ta.current?.focus());
          }}
          className="mt-2 block w-full rounded-md border border-ink/10 bg-amber-50/60 px-2.5 py-1.5 text-left text-sm leading-snug text-ink/80 transition hover:border-ink/20"
          title="Edit note"
        >
          <span className="mr-1.5 inline-block align-middle text-xs">📝</span>
          {notes}
        </button>
      );
    }
    return (
      <button
        type="button"
        onClick={() => {
          setEditing(true);
          queueMicrotask(() => ta.current?.focus());
        }}
        className="mt-2 inline-flex items-center gap-1.5 text-xs text-ink/45 transition hover:text-ink/80"
      >
        <span aria-hidden>📝</span> Add a note
      </button>
    );
  }

  return (
    <div className="mt-2">
      <textarea
        ref={ta}
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        rows={2}
        maxLength={1024}
        placeholder="Buy timed ticket online · wear good shoes · check the courtyard…"
        className="w-full rounded-md border border-ink/15 bg-white px-2.5 py-1.5 text-sm text-ink shadow-sm focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/30"
      />
      <div className="mt-1.5 flex justify-end gap-2 text-xs">
        <button
          type="button"
          onClick={() => {
            setDraft(notes ?? "");
            setEditing(false);
          }}
          className="rounded px-2 py-1 text-ink/60 hover:bg-ink/5"
        >
          Cancel
        </button>
        <button
          type="button"
          disabled={save.isPending}
          onClick={() => save.mutate(draft)}
          className="rounded bg-accent px-3 py-1 font-medium text-white shadow-sm hover:bg-accent-dark disabled:opacity-50"
        >
          {save.isPending ? "Saving…" : "Save"}
        </button>
      </div>
    </div>
  );
}
