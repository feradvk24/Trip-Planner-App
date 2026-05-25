import requests
from functools import lru_cache
from typing import List, NamedTuple, Optional, Tuple

from backend.landmark_registry import Landmark
from backend.tsp_formulas import solve_tsp


class RouteLeg(NamedTuple):
    segments: List[Tuple[float, float]]
    distance_m: float
    duration_s: float


class RouteResult(NamedTuple):
    distance_m: float
    duration_s: float
    legs: List[RouteLeg]


@lru_cache(maxsize=128)
def fetch_route_from_coordinates(coord_pairs: tuple) -> RouteResult:
    """
    Cached OSRM call. coord_pairs is a tuple of (lat, lon) tuples so it is
    hashable and safe to use as an lru_cache key.
    """
    coords = ";".join(f"{lon},{lat}" for lat, lon in coord_pairs)
    url = (
        f"https://router.project-osrm.org/route/v1/driving/"
        f"{coords}?overview=false&geometries=geojson&steps=true"
    )

    res = requests.get(url, timeout=15)
    if res.status_code != 200:
        raise Exception(f"Failed to fetch route: {res.status_code}")

    data = res.json()
    if "routes" not in data or len(data["routes"]) == 0:
        raise Exception("No route found")

    route = data["routes"][0]
    route_legs = []

    for leg in route["legs"]:
        leg_coords = []
        for step in leg["steps"]:
            leg_coords.extend((c[1], c[0]) for c in step["geometry"]["coordinates"])
        route_legs.append(RouteLeg(
            segments=leg_coords,
            distance_m=leg.get("distance", 0),
            duration_s=leg.get("duration", 0),
        ))

    return RouteResult(
        distance_m=route.get("distance", 0),
        duration_s=route.get("duration", 0),
        legs=route_legs,
    )


def fetch_route_steps(
    waypoints: List[Landmark],
    start_point: Optional[Tuple[float, float]] = None,
    end_point: Optional[Tuple[float, float]] = None,
) -> RouteResult:
    coord_pairs = []
    if start_point:
        coord_pairs.append(start_point)
    coord_pairs.extend(w.routing_coordinates() for w in waypoints)
    if end_point:
        coord_pairs.append(end_point)

    if len(coord_pairs) < 2:
        return RouteResult(distance_m=0, duration_s=0, legs=[])
    
    coord_pairs = tuple((float(lat), float(lon)) for lat, lon in coord_pairs)
    if len(coord_pairs) < 2:
        return RouteResult(distance_m=0, duration_s=0, legs=[])
    return fetch_route_from_coordinates(coord_pairs)


def optimize_visit_order(
    points: List[Landmark],
    start_point: Optional[Landmark] = None,
    end_point: Optional[Landmark] = None,
) -> List[Landmark]:
    ordered_landmarks = solve_tsp(points, start_point, end_point)
    return ordered_landmarks

