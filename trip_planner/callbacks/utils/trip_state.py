from dash.exceptions import PreventUpdate

from i18n import t


def _visit_order(trip_data):
    return list((trip_data or {}).get("visit_order") or (trip_data or {}).get("landmark_ids") or [])


def _route_legs(trip_data):
    return list((trip_data or {}).get("route_legs") or [])


def _custom_start_location(trip_data):
    trip_data = trip_data or {}
    return trip_data.get("custom_start_location")


def _custom_end_location(trip_data):
    trip_data = trip_data or {}
    return trip_data.get("custom_end_location")


def destination_ids(trip_data):
    return [
        landmark_id
        for landmark_id in _visit_order(trip_data)
        if landmark_id != -1
    ]


def _stop_count_including_custom_end(trip_data):
    return len(_visit_order(trip_data)) + int(bool(_custom_end_location(trip_data)))


def visited_set(trip_data):
    return set((trip_data or {}).get("visited_indices") or [])


def is_complete(trip_data):
    count = _stop_count_including_custom_end(trip_data)
    visited = visited_set(trip_data)
    return bool(count) and all(i in visited for i in range(count))


def next_action_index(trip_data):
    count = _stop_count_including_custom_end(trip_data)
    if not count or is_complete(trip_data):
        return None
    visited = visited_set(trip_data)
    return next((i for i in range(count) if i not in visited), None)


def active_leg_index(trip_data):
    next_index = next_action_index(trip_data)
    if next_index is None:
        return None
    if next_index == 0 and not _custom_start_location(trip_data):
        return None
    start_offset = int(bool(_custom_start_location(trip_data)))
    return max(0, start_offset + next_index - 1)


def landmark_id_at(trip_data, index):
    visit_order = _visit_order(trip_data)
    if index is None or index < 0 or index >= len(visit_order):
        return None
    landmark_id = visit_order[index]
    return None if landmark_id == -1 else landmark_id


def next_landmark_id(trip_data):
    return landmark_id_at(trip_data, next_action_index(trip_data))


def sanitize_shared_trip(trip):
    route_legs = _route_legs(trip)
    if _custom_start_location(trip):
        route_legs = route_legs[1:]
    if _custom_end_location(trip):
        route_legs = route_legs[:-1]
    route_legs = [
        {
            **leg,
            "from_index": index,
            "to_index": index + 1,
        }
        for index, leg in enumerate(route_legs)
    ]
    return {
        **trip,
        "landmark_ids": destination_ids(trip),
        "visit_order": destination_ids(trip),
        "route_legs": route_legs,
        "custom_start_location": None,
        "custom_end_location": None,
        "saved_user_location": None,
    }


def optimized_trip_from_trip(trip):
    return {
        "visit_order": _visit_order(trip),
        "route_legs": _route_legs(trip),
        "custom_start_location": _custom_start_location(trip),
        "custom_end_location": _custom_end_location(trip),
        "total_distance_m": sum(leg.get("distance_m", 0) for leg in _route_legs(trip)),
        "total_duration_s": sum(leg.get("duration_s", 0) for leg in _route_legs(trip)),
    }


def trip_point_summary(registry, visit_order_ids, index, active_trip=None, lang="bg"):
    active_trip = active_trip or {}
    visit_order = list(visit_order_ids or [])
    if index is None or index < 0:
        return None
    if index == len(visit_order) and _custom_end_location(active_trip):
        return {"name": t("route.my_location", lang=lang), "location": t("trip_status.final_stop", lang=lang)}
    if index >= len(visit_order):
        return None
    landmark_id = visit_order[index]
    if landmark_id == -1:
        return {"name": t("route.my_location", lang=lang), "location": ""}
    landmark = registry.get_landmark(landmark_id)
    if not landmark:
        return {"name": t("trip_status.unknown_destination", lang=lang), "location": ""}
    return {"name": landmark.name, "location": landmark.location}


def visit_stop(active_trip, clicked_index, update_progress):
    if not active_trip or clicked_index is None:
        raise PreventUpdate
    if clicked_index != next_action_index(active_trip):
        raise PreventUpdate
    if clicked_index >= _stop_count_including_custom_end(active_trip):
        raise PreventUpdate

    update_progress(
        trip_id=active_trip["trip_id"],
        new_current_index=clicked_index,
        newly_visited_index=clicked_index,
    )
    visited_indices = list(active_trip.get("visited_indices") or [])
    if clicked_index not in visited_indices:
        visited_indices.append(clicked_index)
    return {
        **active_trip,
        "current_point_index": clicked_index,
        "visited_indices": visited_indices,
    }
