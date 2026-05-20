"""2-opt TSP heuristic for ordering itinerary stops.

Ported from the original DayTour `Plan/services/two_opt.py`. The algorithm is
unchanged; the surface has been cleaned up and divorced from matplotlib /
random module-level imports. The distance source is now pluggable so we can
swap haversine for a Google Distance Matrix call.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt


@dataclass(frozen=True)
class GeoPoint:
    place_id: str
    lat: float
    lon: float


def haversine_km(a: GeoPoint, b: GeoPoint) -> float:
    r = 6371.0
    lat1, lat2 = radians(a.lat), radians(b.lat)
    dlat = lat2 - lat1
    dlon = radians(b.lon - a.lon)
    h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * r * asin(sqrt(h))


def build_distance_matrix(points: Sequence[GeoPoint]) -> list[list[float]]:
    n = len(points)
    m = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine_km(points[i], points[j])
            m[i][j] = m[j][i] = d
    return m


def _path_length(order: list[int], dm: list[list[float]]) -> float:
    n = len(order)
    total = dm[order[-1]][order[0]]
    for i in range(n - 1):
        total += dm[order[i]][order[i + 1]]
    return total


def two_opt(order: list[int], dm: list[list[float]], max_iter: int = 1000) -> list[int]:
    n = len(order)
    improved = True
    it = 0
    while improved and it < max_iter:
        improved = False
        for i in range(n - 1):
            for j in range(i + 2, n):
                delta = (
                    -dm[order[i]][order[i + 1]]
                    - dm[order[j]][order[(j + 1) % n]]
                    + dm[order[i]][order[j]]
                    + dm[order[i + 1]][order[(j + 1) % n]]
                )
                if delta < -1e-12:
                    order[i + 1 : j + 1] = reversed(order[i + 1 : j + 1])
                    improved = True
        it += 1
    return order


def best_path(points: Sequence[GeoPoint]) -> list[str]:
    """Return place_ids ordered to minimize closed-loop distance.

    The first point is treated as the anchor (start = end of the loop).
    """
    if len(points) <= 1:
        return [p.place_id for p in points]

    dm = build_distance_matrix(points)
    initial = list(range(len(points)))
    ordered = two_opt(initial, dm)

    # Rotate so the anchor (index 0) is first.
    anchor = ordered.index(0)
    rotated = ordered[anchor:] + ordered[:anchor]
    rotated.append(rotated[0])
    return [points[i].place_id for i in rotated]
