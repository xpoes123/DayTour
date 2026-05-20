const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api";

function authHeaders(): HeadersInit {
  if (typeof window === "undefined") return {};
  const t = window.localStorage.getItem("daytour_token");
  return t ? { Authorization: `Bearer ${t}` } : {};
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...(init.headers ?? {}),
    },
  });
  if (!r.ok) {
    const text = await r.text();
    throw new Error(`${r.status} ${text}`);
  }
  return r.json() as Promise<T>;
}

export const api = {
  get: <T = unknown>(path: string) => request<T>(path),
  post: <T = unknown>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
};

export type Stop = {
  position: number;
  place_id: string;
  name: string;
  latitude: number | null;
  longitude: number | null;
  photo_url: string | null;
  rating: number | null;
};

export type Itinerary = {
  id: number;
  title: string | null;
  start_loc: string;
  radius_m: number;
  transit_mode: "walking" | "driving" | "bicycling" | "transit";
  share_token: string | null;
  created_at: string;
  stops: Stop[];
};
