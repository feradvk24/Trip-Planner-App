import requests
from functools import lru_cache
from typing import List, NamedTuple, Optional, Tuple

from backend.api_client import post_json_to_endpoint
from backend.landmark_registry import Landmark
from backend.tsp_formulas import solve_tsp


class RouteResult(NamedTuple):
    segments: List[List[Tuple[float, float]]]
    distance_m: float
    duration_s: float
    legs: List[dict]


def route_result_to_dict(result: RouteResult) -> dict:
    return {
        "segments": result.segments,
        "distance_m": result.distance_m,
        "duration_s": result.duration_s,
        "legs": result.legs,
    }


def route_result_from_dict(data: dict) -> RouteResult:
    return RouteResult(
        segments=data.get("segments", []),
        distance_m=data.get("distance_m", 0),
        duration_s=data.get("duration_s", 0),
        legs=data.get("legs", []),
    )


def _normalize_coord_pairs(coord_pairs) -> tuple:
    return tuple((float(lat), float(lon)) for lat, lon in coord_pairs)


@lru_cache(maxsize=128)
def _fetch_route_cached(coord_pairs: tuple) -> RouteResult:
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
    road_segments = []
    route_legs = []

    for leg in route["legs"]:
        leg_coords = []
        for step in leg["steps"]:
            leg_coords.extend((c[1], c[0]) for c in step["geometry"]["coordinates"])
        if leg_coords:
            road_segments.append(leg_coords)
        route_legs.append({
            "distance_m": leg.get("distance", 0),
            "duration_s": leg.get("duration", 0),
        })

    return RouteResult(
        segments=road_segments,
        distance_m=route.get("distance", 0),
        duration_s=route.get("duration", 0),
        legs=route_legs,
    )


def fetch_route_steps_from_coordinates(coord_pairs) -> RouteResult:
    coord_pairs = _normalize_coord_pairs(coord_pairs)
    if len(coord_pairs) < 2:
        return RouteResult(segments=[], distance_m=0, duration_s=0, legs=[])
    return _fetch_route_cached(coord_pairs)


def _post_route_to_flask_endpoint(coord_pairs: tuple) -> RouteResult:
    payload = {
        "coordinates": [
            {"lat": lat, "lon": lon}
            for lat, lon in coord_pairs
        ]
    }
    data = post_json_to_endpoint(
        "/api/routes/osrm-trip-routing",
        payload,
        "ROUTE_API_URL",
        "Route API returned an error",
    )
    if data is None:
        return fetch_route_steps_from_coordinates(coord_pairs)
    return route_result_from_dict(data)


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
        return RouteResult(segments=[], distance_m=0, duration_s=0, legs=[])
    return _post_route_to_flask_endpoint(_normalize_coord_pairs(coord_pairs))


def _endpoint_payload(point: Optional[Landmark]) -> Optional[dict]:
    if point is None:
        return None
    if point.id == -1:
        return {
            "type": "coordinate",
            "lat": point.lat,
            "lon": point.lon,
            "name": point.name,
        }
    return {"type": "landmark", "id": point.id}


def _post_optimize_to_flask_endpoint(payload: dict) -> list[int]:
    data = post_json_to_endpoint(
        "/api/trips/optimize-visit-order",
        payload,
        "OPTIMIZE_VISIT_ORDER_API_URL",
        "Trip API returned an error",
    )
    if data is None:
        return []
    return data.get("visit_order", [])


def optimize_visit_order(
    points: List[Landmark],
    start_point: Optional[Landmark] = None,
    end_point: Optional[Landmark] = None,
) -> List[int]:
    payload = {
        "landmark_ids": [point.id for point in points],
        "start_point": _endpoint_payload(start_point),
        "end_point": _endpoint_payload(end_point),
    }
    visit_order = _post_optimize_to_flask_endpoint(payload)
    if visit_order:
        return visit_order
    return [landmark.id for landmark in solve_tsp(points, start_point, end_point)]


def generate_route(
    points: List[Landmark],
    start_point: Optional[Landmark] = None,
    end_point: Optional[Landmark] = None,
) -> RouteResult:
    if len(points) < 2:
        return RouteResult(segments=[], distance_m=0, duration_s=0, legs=[])

    route = solve_tsp(points, start_point, end_point)
    return fetch_route_steps(route)
