const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api";
const TOKEN_KEY = "daytour_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(t: string | null) {
  if (typeof window === "undefined") return;
  if (t) window.localStorage.setItem(TOKEN_KEY, t);
  else window.localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  constructor(public status: number, public body: string) {
    super(`${status} ${body}`);
  }
}

function authHeaders(): HeadersInit {
  const t = getToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

async function request<T>(
  path: string,
  init: RequestInit = {},
  contentType: string = "application/json",
): Promise<T> {
  const headers: HeadersInit = {
    ...(contentType ? { "Content-Type": contentType } : {}),
    ...authHeaders(),
    ...(init.headers ?? {}),
  };
  const r = await fetch(`${BASE}${path}`, { ...init, headers });
  if (!r.ok) {
    const text = await r.text();
    if (r.status === 401 && typeof window !== "undefined" && !path.startsWith("/auth/")) {
      setToken(null);
      const next = encodeURIComponent(window.location.pathname + window.location.search);
      window.location.href = `/auth?next=${next}`;
    }
    let msg = text;
    try {
      const j = JSON.parse(text);
      if (j.detail) msg = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
    } catch {}
    throw new ApiError(r.status, msg);
  }
  return r.json() as Promise<T>;
}

export const api = {
  get: <T = unknown>(path: string) => request<T>(path),
  post: <T = unknown>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
};

export type PlaceSuggestion = {
  place_id: string;
  label: string;
  primary: string;
};

export const auth = {
  async register(body: { username: string; email: string; password: string }) {
    await request("/auth/register", { method: "POST", body: JSON.stringify(body) });
  },
  async login(username: string, password: string) {
    const form = new URLSearchParams({ username, password });
    const r = await fetch(`${BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form.toString(),
    });
    if (!r.ok) {
      const text = await r.text();
      let msg = text;
      try {
        msg = JSON.parse(text).detail ?? text;
      } catch {}
      throw new ApiError(r.status, msg);
    }
    const { access_token } = (await r.json()) as { access_token: string };
    setToken(access_token);
    return access_token;
  },
  logout() {
    setToken(null);
  },
};

export type Stop = {
  position: number;
  place_id: string;
  name: string;
  latitude: number | null;
  longitude: number | null;
  photo_url: string | null;
  rating: number | null;
  travel_minutes_from_prev: number | null;
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
  total_travel_minutes: number;
  route_geometry: [number, number][] | null;
};

export function formatMinutes(mins: number): string {
  if (mins < 60) return `${mins} min`;
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return m === 0 ? `${h} hr` : `${h} hr ${m} min`;
}
