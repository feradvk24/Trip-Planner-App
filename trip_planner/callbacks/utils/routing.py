from backend.routing_service import fetch_route_steps
from backend.landmark_registry import Landmark


def resolve_endpoint(registry, point_id, position):
    if point_id == "my_location" and position:
        return Landmark(id=-1, name="My location", location="", lat=position["lat"], lon=position["lon"])
    if point_id and point_id != "auto":
        return registry.get_landmark(int(point_id))
    return None


def location_tuple(location):
    if not location:
        return None
    return location["lat"], location["lon"]


def resolve_visit_order_landmarks(registry, visit_order_ids, position=None):
    visit_order_lms = []
    for landmark_id in visit_order_ids or []:
        if landmark_id == -1:
            if position:
                visit_order_lms.append(
                    Landmark(
                        id=-1,
                        name="My location",
                        location="",
                        lat=position["lat"],
                        lon=position["lon"],
                    )
                )
            continue
        landmark = registry.get_landmark(landmark_id)
        if landmark:
            visit_order_lms.append(landmark)
    return visit_order_lms


def build_route_legs(route_point_count, route_result):
    # Indexes refer to the composed route:
    # [custom_start?] + visit_order landmarks + [custom_end?].
    return [
        {
            "from_index": i,
            "to_index": i + 1,
            "distance_m": leg.get("distance_m", 0),
            "duration_s": leg.get("duration_s", 0),
        }
        for i, leg in enumerate(route_result.legs)
        if i + 1 < route_point_count
    ]


def format_distance(distance_m):
    if distance_m is None:
        return "Unknown"
    if distance_m >= 1000:
        return f"{distance_m / 1000:.1f} km"
    return f"{int(round(distance_m))} m"


def get_route_legs(registry, active_trip):
    route_legs = active_trip.get("route_legs") or []
    if route_legs:
        return route_legs
    stop_ids = active_trip.get("visit_order") or []
    custom_start = active_trip.get("custom_start_location")
    custom_end = active_trip.get("custom_end_location")
    try:
        route_result = fetch_route_steps(
            registry.get_landmarks(stop_ids),
            start_point=location_tuple(custom_start),
            end_point=location_tuple(custom_end),
        )
        route_point_count = len(stop_ids) + int(bool(custom_start)) + int(bool(custom_end))
        return build_route_legs(route_point_count, route_result)
    except Exception:
        return []
