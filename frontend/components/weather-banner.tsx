"use client";

import { useQuery } from "@tanstack/react-query";
import { api, type Weather } from "@/lib/api";

export function useWeather(
  lat: number | null | undefined,
  lon: number | null | undefined,
  date: string,
) {
  return useQuery<Weather | null>({
    queryKey: ["weather", lat, lon, date],
    enabled: lat != null && lon != null,
    staleTime: 20 * 60 * 1000,
    queryFn: async () => {
      if (lat == null || lon == null) return null;
      try {
        return await api.get<Weather>(
          `/weather?lat=${lat}&lon=${lon}&date=${date}`,
        );
      } catch {
        return null;
      }
    },
  });
}

export function WeatherBanner({ weather }: { weather: Weather }) {
  return (
    <div className="inline-flex items-center gap-3 rounded-lg border border-ink/10 bg-white px-3 py-2 text-sm shadow-sm">
      <span aria-hidden className="text-2xl leading-none">
        {weather.icon}
      </span>
      <div className="flex flex-col">
        <div className="flex items-baseline gap-1.5">
          <span className="font-semibold tabular-nums text-ink">
            {weather.high_f}°
          </span>
          <span className="text-ink/50">/</span>
          <span className="tabular-nums text-ink/60">{weather.low_f}°</span>
          <span className="ml-1 text-ink/70">{weather.label}</span>
        </div>
        {weather.precip_chance > 0 && (
          <div className="text-xs text-ink/55">
            {weather.precip_chance}% chance of precipitation
          </div>
        )}
      </div>
    </div>
  );
}

export function HourChip({ hour }: { hour: import("@/lib/api").WeatherHour }) {
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full bg-ink/5 px-2 py-0.5 text-xs text-ink/70"
      title={`${hour.label} · ${hour.precip_chance}% precip`}
    >
      <span aria-hidden>{hour.icon}</span>
      <span className="tabular-nums">{hour.temp_f}°</span>
    </span>
  );
}
