from dash.exceptions import PreventUpdate

from i18n import t
from services.trip_route import TripRoute


def _custom_start_location(trip_data):
    return TripRoute.handle_trip_store(trip_data)["custom_start_location"]


def _custom_end_location(trip_data):
    return TripRoute.handle_trip_store(trip_data)["custom_end_location"]


def sanitize_shared_trip(trip):
    store = TripRoute.handle_trip_store(trip)
    route_legs = store["route_legs"]
    if store["custom_start_location"]:
        route_legs = route_legs[1:]
    if store["custom_end_location"]:
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
        "landmark_ids": store["destination_ids"],
        "visit_order": store["destination_ids"],
        "route_legs": route_legs,
        "custom_start_location": None,
        "custom_end_location": None,
        "saved_user_location": None,
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


def visit_stop(active_trip, clicked_index, update_progress, route=None):
    if not active_trip or clicked_index is None:
        raise PreventUpdate
    route = route or TripRoute.from_store(active_trip)
    try:
        route.visit(clicked_index)
    except ValueError:
        raise PreventUpdate

    update_progress(
        trip_id=active_trip["trip_id"],
        new_current_index=clicked_index,
        newly_visited_index=clicked_index,
    )
    return {
        **active_trip,
        "current_point_index": clicked_index,
        "visited_indices": sorted(route.visited_indices),
    }
