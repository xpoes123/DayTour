const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api";
const TOKEN_KEY = "daytour_token";

/** Turn a backend-relative photo URL ('/api/places/X/photo') into a fully-qualified one. */
export function photoSrc(photoUrl: string | null | undefined): string | null {
  if (!photoUrl) return null;
  if (photoUrl.startsWith("http")) return photoUrl;
  const origin = BASE.replace(/\/api\/?$/, "");
  return origin + photoUrl;
}

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

export type Alternative = {
  place_id: string;
  name: string;
  latitude: number | null;
  longitude: number | null;
  photo_url: string | null;
  rating: number | null;
};

export type Restaurant = {
  place_id: string;
  name: string;
  rating: number | null;
  price_level: string | null;
  address: string | null;
  photo_url: string | null;
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

export type TravelStep = {
  mode: "walk" | "bus" | "subway" | "rail";
  duration_sec: number;
  distance_m: number;
  label: string | null;
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
  travel_steps_from_prev: TravelStep[];
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
  summary: string | null;
};

export function formatMinutes(mins: number): string {
  if (mins < 60) return `${mins} min`;
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return m === 0 ? `${h} hr` : `${h} hr ${m} min`;
}

/** Rough dwell time at a place based on its name. Tourists optimize ergonomics, not accuracy. */
export function dwellMinutes(name: string): number {
  const n = name.toLowerCase();
  if (/(museum|art|gallery|aquarium|planetarium|library)\b/.test(n)) return 90;
  if (/(park|garden|trail|point|beach|preserve|reserve|lookout|overlook)\b/.test(n)) return 60;
  if (/(restaurant|cafe|coffee|brewery|bar|pub|diner|bistro)\b/.test(n)) return 75;
  if (/(zoo|market|stadium|arena|theater|theatre|cathedral|temple|mosque|shrine)\b/.test(n))
    return 75;
  if (/(square|plaza|monument|memorial|tower|bridge|statue|fountain|observatory)\b/.test(n))
    return 30;
  return 45;
}

/** Format a Date as a local clock-time like "10:30 AM". */
export function formatClock(d: Date): string {
  return d.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
}

/** Walk the stops to assign arrival/depart times given a start clock-time (HH:mm). */
export type ScheduledStop = {
  arrival: Date;
  depart: Date;
};

export function computeSchedule(
  stops: Stop[],
  startHHMM: string,
): ScheduledStop[] {
  const [h, m] = startHHMM.split(":").map((v) => Number.parseInt(v, 10));
  const cursor = new Date();
  cursor.setHours(h, m, 0, 0);
  const out: ScheduledStop[] = [];
  for (let i = 0; i < stops.length; i++) {
    const s = stops[i];
    if (i > 0 && s.travel_minutes_from_prev != null) {
      cursor.setMinutes(cursor.getMinutes() + s.travel_minutes_from_prev);
    }
    const arrival = new Date(cursor);
    const dwell = dwellMinutes(s.name);
    cursor.setMinutes(cursor.getMinutes() + dwell);
    const depart = new Date(cursor);
    out.push({ arrival, depart });
  }
  return out;
}
