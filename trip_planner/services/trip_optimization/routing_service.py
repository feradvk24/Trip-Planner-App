import requests
from functools import lru_cache
from typing import List, NamedTuple, Optional, Tuple

import polyline

from services.landmark_registry import Landmark
from services.trip_optimization.tsp_formulas import (
    haversine,
    nearest_neighbor,
    route_distance,
    two_opt,
    two_opt_by_distance,
)


class RouteLeg(NamedTuple):
    polyline: str
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
        f"{coords}?overview=false&geometries=polyline&steps=true"
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
            geometry = step.get("geometry")
            if isinstance(geometry, str):
                step_coords = polyline.decode(geometry)
            else:
                step_coords = [
                    (c[1], c[0])
                    for c in (geometry or {}).get("coordinates", [])
                ]

            if leg_coords and step_coords and leg_coords[-1] == step_coords[0]:
                leg_coords.extend(step_coords[1:])
            else:
                leg_coords.extend(step_coords)

        route_legs.append(RouteLeg(
            polyline=polyline.encode(leg_coords) if leg_coords else "",
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
    fetch_route_steps: bool = True,
) -> RouteResult:
    route_points = []
    if start_point:
        route_points.append(Landmark(id=-1, name="", location="", lat=start_point[0], lon=start_point[1]))
    route_points.extend(waypoints)
    if end_point:
        route_points.append(Landmark(id=-1, name="", location="", lat=end_point[0], lon=end_point[1]))

    if len(route_points) < 2:
        return RouteResult(distance_m=0, duration_s=0, legs=[])

    coord_pairs = tuple(
        (float(lat), float(lon))
        for lat, lon in (point.routing_coordinates() for point in route_points)
    )
    if not fetch_route_steps:
        legs = [
            RouteLeg(
                polyline=polyline.encode([coord_pairs[i], coord_pairs[i + 1]]),
                distance_m=haversine(route_points[i], route_points[i + 1]) * 1000,
                duration_s=0,
            )
            for i in range(len(route_points) - 1)
        ]
        return RouteResult(
            distance_m=sum(leg.distance_m for leg in legs),
            duration_s=0,
            legs=legs,
        )
    return fetch_route_from_coordinates(coord_pairs)


def optimize_visit_order(
    points: List[Landmark],
    start_point: Optional[Landmark] = None,
    end_point: Optional[Landmark] = None,
    use_multistart: bool = True,
    use_two_opt: bool = True,
) -> List[Landmark]:
    if not points:
        return []

    if start_point:
        route = nearest_neighbor(points, start_point, end_point)
        if use_two_opt:
            route = two_opt(route, haversine, fix_start=True, fix_end=bool(end_point))
        return route

    if not use_multistart:
        route = nearest_neighbor(points, end_point=end_point)
        if use_two_opt:
            route = two_opt_by_distance(route, fix_start=False, fix_end=bool(end_point))
        return route

    best_route = None
    best_distance = float("inf")
    for candidate_start in points:
        route = nearest_neighbor(points, candidate_start, end_point)
        if use_two_opt:
            route = two_opt_by_distance(route, fix_start=False, fix_end=bool(end_point))
        distance = route_distance(route)
        if distance < best_distance:
            best_distance = distance
            best_route = route

    return best_route or []
