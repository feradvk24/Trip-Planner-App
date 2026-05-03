from dash.exceptions import PreventUpdate


def sanitize_shared_trip(trip):
    landmark_ids = [landmark_id for landmark_id in (trip.get("landmark_ids") or []) if landmark_id != -1]
    visit_order = [landmark_id for landmark_id in (trip.get("visit_order") or landmark_ids) if landmark_id != -1]
    has_private_endpoint = bool(trip.get("custom_start_location") or trip.get("custom_end_location"))
    return {
        **trip,
        "landmark_ids": landmark_ids,
        "visit_order": visit_order,
        "route_legs": [] if has_private_endpoint else trip.get("route_legs", []),
        "custom_start_location": None,
        "custom_end_location": None,
        "saved_user_location": None,
    }


def clamp_stop_index(active_trip):
    stop_ids = active_trip.get("visit_order") or []
    if not stop_ids:
        return 0
    return max(0, min(active_trip.get("current_point_index", 0), len(stop_ids) - 1))


def trip_complete(active_trip):
    stop_ids = active_trip.get("visit_order") or []
    visited = set(active_trip.get("visited_indices") or [])
    return bool(stop_ids) and all(i in visited for i in range(len(stop_ids)))


def next_action_stop_index(active_trip):
    stop_ids = active_trip.get("visit_order") or []
    if not stop_ids or trip_complete(active_trip):
        return None
    visited = set(active_trip.get("visited_indices") or [])
    return next((i for i in range(len(stop_ids)) if i not in visited), None)


def active_route_leg_index(active_trip):
    next_idx = next_action_stop_index(active_trip)
    if next_idx is None:
        return None
    start_offset = 1 if active_trip.get("custom_start_location") else 0
    return max(0, start_offset + next_idx - 1)


def trip_point_summary(registry, visit_order_ids, index):
    if index is None or index < 0 or index >= len(visit_order_ids):
        return None
    landmark_id = visit_order_ids[index]
    if landmark_id == -1:
        return {"name": "My location", "location": ""}
    landmark = registry.get_landmark(landmark_id)
    if not landmark:
        return {"name": "Unknown destination", "location": ""}
    return {"name": landmark.name, "location": landmark.location}


def visit_stop(active_trip, clicked_index, current_username, update_progress):
    if not active_trip or clicked_index is None:
        raise PreventUpdate
    stop_ids = active_trip.get("visit_order") or []
    if clicked_index != next_action_stop_index(active_trip):
        raise PreventUpdate
    if clicked_index >= len(stop_ids):
        raise PreventUpdate

    if active_trip.get("owner_username", current_username) == current_username:
        update_progress(
            trip_id=active_trip["trip_id"],
            new_current_index=clicked_index,
            newly_visited_index=clicked_index,
        )
    visited = list(active_trip.get("visited_indices") or [])
    if clicked_index not in visited:
        visited.append(clicked_index)
    return {
        **active_trip,
        "current_point_index": clicked_index,
        "visited_indices": visited,
    }
