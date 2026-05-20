"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api, photoSrc, type Restaurant } from "@/lib/api";

const PRICE_LABEL: Record<string, string> = {
  PRICE_LEVEL_FREE: "Free",
  PRICE_LEVEL_INEXPENSIVE: "$",
  PRICE_LEVEL_MODERATE: "$$",
  PRICE_LEVEL_EXPENSIVE: "$$$",
  PRICE_LEVEL_VERY_EXPENSIVE: "$$$$",
};

export function NearbyRestaurants({
  itineraryId,
  placeId,
}: {
  itineraryId: number;
  placeId: string;
}) {
  const [open, setOpen] = useState(false);
  const { data, isLoading } = useQuery<Restaurant[]>({
    queryKey: ["restaurants", itineraryId, placeId],
    queryFn: () => api.get(`/itineraries/${itineraryId}/stops/${placeId}/restaurants`),
    enabled: open,
    staleTime: 5 * 60 * 1000,
  });

  return (
    <div className="mt-2 border-t border-ink/5 pt-2">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between text-xs font-medium text-ink/60 hover:text-ink"
      >
        <span className="inline-flex items-center gap-1.5">
          <span aria-hidden>🍽</span> Eat near here
        </span>
        <span className="text-ink/40">{open ? "−" : "+"}</span>
      </button>
      {open && (
        <div className="mt-2">
          {isLoading && <div className="text-xs text-ink/40">Finding spots…</div>}
          {data && data.length === 0 && (
            <div className="text-xs text-ink/40">No restaurants close by.</div>
          )}
          {data && data.length > 0 && (
            <ul className="flex flex-col gap-1.5">
              {data.map((r) => {
                const img = photoSrc(r.photo_url);
                const price = r.price_level ? PRICE_LABEL[r.price_level] : null;
                return (
                  <li
                    key={r.place_id}
                    className="flex items-center gap-2 rounded-md border border-ink/10 bg-white p-1.5"
                  >
                    {img ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={img}
                        alt=""
                        loading="lazy"
                        className="h-10 w-10 flex-shrink-0 rounded object-cover"
                        onError={(e) => {
                          (e.currentTarget as HTMLImageElement).style.display = "none";
                        }}
                      />
                    ) : (
                      <div className="h-10 w-10 flex-shrink-0 rounded bg-ink/5" />
                    )}
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-medium text-ink">{r.name}</div>
                      <div className="flex items-center gap-2 text-xs text-ink/60">
                        {r.rating != null && <span>★ {r.rating.toFixed(1)}</span>}
                        {price && <span>{price}</span>}
                        {r.address && (
                          <span className="truncate text-ink/40">{r.address.split(",")[0]}</span>
                        )}
                      </div>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
