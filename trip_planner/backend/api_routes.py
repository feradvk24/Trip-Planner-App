from flask import jsonify, request

from backend.landmark_registry import Landmark
from backend.routing_service import (
    fetch_route_steps_from_coordinates,
    route_result_to_dict,
)
from backend.tsp_formulas import solve_tsp


MAX_ROUTE_COORDINATES = 100
MAX_OPTIMIZE_LANDMARKS = 100


def _parse_coordinate(coordinate, field_name):
    try:
        lat = float(coordinate["lat"])
        lon = float(coordinate["lon"])
    except (KeyError, TypeError, ValueError):
        raise ValueError(f"{field_name} must include numeric lat and lon")

    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise ValueError(f"{field_name} is out of range")

    return lat, lon


def _resolve_trip_endpoint(registry, endpoint, field_name):
    if not endpoint or endpoint.get("type") == "auto":
        return None

    endpoint_type = endpoint.get("type")
    if endpoint_type == "landmark":
        try:
            landmark_id = int(endpoint["id"])
        except (KeyError, TypeError, ValueError):
            raise ValueError(f"{field_name} landmark id is invalid")

        landmark = registry.get_landmark(landmark_id)
        if landmark is None:
            raise ValueError(f"{field_name} landmark was not found")
        return landmark

    if endpoint_type in ("coordinate", "my_location"):
        lat, lon = _parse_coordinate(endpoint, field_name)
        return Landmark(
            id=-1,
            name=endpoint.get("name") or "Custom location",
            location="",
            lat=lat,
            lon=lon,
        )

    raise ValueError(f"{field_name} type is invalid")


def register_api_routes(server, registry):
    @server.post("/api/routes/osrm-trip-routing")
    def osrm_trip_routing():
        payload = request.get_json(silent=True) or {}
        coordinates = payload.get("coordinates")

        if not isinstance(coordinates, list):
            return jsonify({"error": "coordinates must be a list"}), 400
        if len(coordinates) < 2:
            return jsonify({"error": "at least two coordinates are required"}), 400
        if len(coordinates) > MAX_ROUTE_COORDINATES:
            return jsonify({"error": f"at most {MAX_ROUTE_COORDINATES} coordinates are allowed"}), 400

        coord_pairs = []
        for index, coordinate in enumerate(coordinates):
            try:
                lat, lon = _parse_coordinate(coordinate, f"coordinate at index {index}")
            except ValueError as exc:
                return jsonify({"error": str(exc)}), 400

            coord_pairs.append((lat, lon))

        try:
            result = fetch_route_steps_from_coordinates(tuple(coord_pairs))
        except Exception as exc:
            return jsonify({"error": str(exc)}), 502

        return jsonify(route_result_to_dict(result))

    @server.post("/api/trips/optimize-visit-order")
    def optimize_visit_order():
        payload = request.get_json(silent=True) or {}
        landmark_ids = payload.get("landmark_ids")

        if not isinstance(landmark_ids, list):
            return jsonify({"error": "landmark_ids must be a list"}), 400
        if len(landmark_ids) < 2:
            return jsonify({"error": "at least two landmarks are required"}), 400
        if len(landmark_ids) > MAX_OPTIMIZE_LANDMARKS:
            return jsonify({"error": f"at most {MAX_OPTIMIZE_LANDMARKS} landmarks are allowed"}), 400

        landmarks = []
        for index, landmark_id in enumerate(landmark_ids):
            try:
                landmark_id = int(landmark_id)
            except (TypeError, ValueError):
                return jsonify({"error": f"invalid landmark id at index {index}"}), 400

            landmark = registry.get_landmark(landmark_id)
            if landmark is None:
                return jsonify({"error": f"landmark {landmark_id} was not found"}), 404
            landmarks.append(landmark)

        try:
            start_point = _resolve_trip_endpoint(registry, payload.get("start_point"), "start_point")
            end_point = _resolve_trip_endpoint(registry, payload.get("end_point"), "end_point")
            visit_order = solve_tsp(landmarks, start_point=start_point, end_point=end_point)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        return jsonify({"visit_order": [landmark.id for landmark in visit_order]})
