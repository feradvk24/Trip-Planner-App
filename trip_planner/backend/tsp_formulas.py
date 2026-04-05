import requests
import math
import requests
from math import radians, cos, sin, asin, sqrt
from typing import List, Optional, Tuple, NamedTuple

from marker_config import Landmark

def haversine(a: Landmark, b: Landmark) -> float:
    """
    Calculate the great-circle distance between two points on the Earth using Haversine formula.
    Returns distance in kilometers.
    """
    R = 6371  # Earth radius in km

    dlat = math.radians(b.lat - a.lat)
    dlon = math.radians(b.lon - a.lon)

    sa = math.sin(dlat / 2)
    sb = math.sin(dlon / 2)

    h = sa * sa + math.cos(math.radians(a.lat)) * math.cos(math.radians(b.lat)) * sb * sb

    distance = 2 * R * math.asin(math.sqrt(h))
    return distance


def nearest_neighbor(
    points: List[Landmark],
    start_point: Optional[Landmark] = None,
    end_point: Optional[Landmark] = None
) -> List[Landmark]:
    remaining = points.copy()

    is_round_trip = end_point and start_point and end_point.id == start_point.id

    remaining_ids = {m.id for m in remaining}
    start_in_list = start_point and start_point.id in remaining_ids
    end_in_list = end_point and not is_round_trip and end_point.id in remaining_ids

    if start_in_list:
        for i, m in enumerate(remaining):
            if m.id == start_point.id:
                route = [remaining.pop(i)]
                break
    elif start_point:
        # External start point (e.g. user's current location) — not a destination
        route = [start_point]
    else:
        route = [remaining.pop(0)]

    end_landmark = None
    if end_in_list:
        for i, m in enumerate(remaining):
            if m.id == end_point.id:
                end_landmark = remaining.pop(i)
                break

    while remaining:
        last = route[-1]
        nearest_idx = 0
        nearest_dist = float("inf")

        for i in range(len(remaining)):
            d = haversine(last, remaining[i])

            if d < nearest_dist:
                nearest_dist = d
                nearest_idx = i

        route.append(remaining.pop(nearest_idx))

    if end_in_list and end_landmark:
        route.append(end_landmark)
    elif is_round_trip:
        # Close the loop: return to the start point
        route.append(route[0])
    elif end_point and not end_in_list:
        # External end point (e.g. user's current location) — not a destination
        route.append(end_point)

    return route


def two_opt(route, distance_func, fix_start=True, fix_end=False):
    """
    Improve a route using the 2-opt heuristic.

    route: list of nodes (Monument objects)
    distance_func: function(a, b) -> distance
    fix_start: keep first node fixed
    fix_end: keep last node fixed
    """
    improved = True
    n = len(route)

    while improved:
        improved = False

        i_start = 1 if fix_start else 0
        j_end = n - 1 if fix_end else n

        for i in range(i_start, n - 2):
            for j in range(i + 1, j_end):

                a = route[i - 1]
                b = route[i]
                c = route[j]
                d = route[j + 1] if j + 1 < n else None

                if d is None:
                    continue

                d1 = distance_func(a, b) + distance_func(c, d)
                d2 = distance_func(a, c) + distance_func(b, d)

                if d2 < d1:
                    route[i:j + 1] = reversed(route[i:j + 1])
                    improved = True

    return route

class RouteResult(NamedTuple):
    segments: List[List[Tuple[float, float]]]
    distance_m: float   # total distance in metres
    duration_s: float   # total duration in seconds

def fetch_route_steps(waypoints: List[Landmark]) -> RouteResult:
    """
    Returns road segments together with total distance and duration from OSRM.
    """
    if len(waypoints) < 2:
        return RouteResult(segments=[], distance_m=0, duration_s=0)

    # Build OSRM coordinates string
    coords = ";".join(f"{w.lon},{w.lat}" for w in waypoints)
    url = (
        f"https://router.project-osrm.org/route/v1/driving/"
        f"{coords}?overview=false&geometries=geojson&steps=true"
    )

    res = requests.get(url)
    if res.status_code != 200:
        raise Exception(f"Failed to fetch route: {res.status_code}")

    data = res.json()
    if "routes" not in data or len(data["routes"]) == 0:
        raise Exception("No route found")

    route = data["routes"][0]
    road_segments = []

    # Iterate over each leg (between consecutive waypoints)
    for leg in route["legs"]:
        # Iterate over each step (road segment)
        for step in leg["steps"]:
            coords_step = [(c[1], c[0]) for c in step["geometry"]["coordinates"]]  # lat, lon
            road_segments.append(coords_step)

    return RouteResult(
        segments=road_segments,
        distance_m=route.get("distance", 0),
        duration_s=route.get("duration", 0),
    )


def solve_tsp(
    points: List[Landmark],
    start_point: Optional[Landmark] = None,
    end_point: Optional[Landmark] = None
) -> List[Landmark]:
    route = nearest_neighbor(points, start_point, end_point)
    route = two_opt(route, haversine, fix_start=bool(start_point), fix_end=bool(end_point))
    return route


def generate_route(
        points: List[Landmark],
        start_point: Optional[Landmark] = None,
        end_point: Optional[Landmark] = None
) -> List[List[Tuple[float, float]]]:
    if len(points) < 2:
        return []

    route = solve_tsp(points, start_point, end_point)
    return fetch_route_steps(route)