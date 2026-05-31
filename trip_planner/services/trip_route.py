from dataclasses import dataclass, field
from typing import Optional

from dash_store_schemas.stores import ActiveTripStore, LocationStore, OptimizedTripStore, RouteLegStore
from services.landmark_registry import Landmark


@dataclass(frozen=True)
class RouteNode:
    kind: str
    landmark_id: Optional[int] = None
    location: Optional[LocationStore] = None

    @classmethod
    def landmark(cls, landmark_id):
        return cls(kind="landmark", landmark_id=landmark_id)

    @classmethod
    def custom_start(cls, location):
        return cls(kind="custom_start", location=location)

    @classmethod
    def custom_end(cls, location):
        return cls(kind="custom_end", location=location)

    @property
    def is_action_stop(self):
        return self.kind != "custom_start"

    @property
    def is_landmark(self):
        return self.kind == "landmark"


@dataclass
class TripRoute:
    nodes: list[RouteNode]
    route_legs: list[RouteLegStore] = field(default_factory=list)
    visited_indices: set[int] = field(default_factory=set)

    @classmethod
    def handle_trip_store(cls, trip_data: ActiveTripStore | OptimizedTripStore | None) -> dict:
        trip_data = trip_data or {}
        visit_order = [
            landmark_id
            for landmark_id in (trip_data.get("visit_order") or trip_data.get("landmark_ids") or [])
            if landmark_id != -1
        ]
        route_legs = list(trip_data.get("route_legs") or [])
        custom_start = trip_data.get("custom_start_location")
        custom_end = trip_data.get("custom_end_location")
        visited_indices = list(trip_data.get("visited_indices") or [])
        return {
            "visit_order": visit_order,
            "destination_ids": list(visit_order),
            "route_legs": route_legs,
            "custom_start_location": custom_start,
            "custom_end_location": custom_end,
            "visited_indices": visited_indices,
            "visited_set": set(visited_indices),
            "action_stop_count": len(visit_order) + int(bool(custom_end)),
            "total_distance_m": sum(leg.get("distance_m", 0) for leg in route_legs),
            "total_duration_s": sum(leg.get("duration_s", 0) for leg in route_legs),
        }

    @classmethod
    def optimized(
        cls,
        landmarks: list[Landmark],
        start_point: Optional[Landmark] = None,
        end_point: Optional[Landmark] = None,
        use_multistart: bool = True,
        use_two_opt: bool = True,
        fetch_route_steps: bool = True,
    ):
        from services.trip_optimization.routing_service import fetch_route_steps as get_route_steps, optimize_visit_order

        custom_start = _custom_location(start_point)
        custom_end = _custom_location(end_point)
        visit_order = [
            landmark
            for landmark in optimize_visit_order(
                landmarks,
                start_point=start_point,
                end_point=end_point,
                use_multistart=use_multistart,
                use_two_opt=use_two_opt,
            )
            if landmark.id != -1
        ]
        route_result = get_route_steps(
            visit_order,
            start_point=_location_tuple(custom_start),
            end_point=_location_tuple(custom_end),
            fetch_route_steps=fetch_route_steps,
        )
        nodes = [
            *([RouteNode.custom_start(custom_start)] if custom_start else []),
            *(RouteNode.landmark(landmark.id) for landmark in visit_order),
            *([RouteNode.custom_end(custom_end)] if custom_end else []),
        ]
        return cls(
            nodes=nodes,
            route_legs=_route_leg_dicts(len(nodes), route_result),
        )

    @classmethod
    def from_store(cls, trip_data: ActiveTripStore | OptimizedTripStore | None):
        store = cls.handle_trip_store(trip_data)
        nodes = [
            *([RouteNode.custom_start(store["custom_start_location"])] if store["custom_start_location"] else []),
            *(RouteNode.landmark(landmark_id) for landmark_id in store["visit_order"]),
            *([RouteNode.custom_end(store["custom_end_location"])] if store["custom_end_location"] else []),
        ]
        return cls(
            nodes=nodes,
            route_legs=store["route_legs"],
            visited_indices=store["visited_set"],
        )

    @property
    def action_nodes(self):
        return [node for node in self.nodes if node.is_action_stop]

    @property
    def action_stop_count(self):
        return len(self.action_nodes)

    @property
    def action_node_path_indices(self):
        return [
            index
            for index, node in enumerate(self.nodes)
            if node.is_action_stop
        ]

    @property
    def visit_order(self):
        return [
            node.landmark_id
            for node in self.action_nodes
            if node.is_landmark
        ]

    @property
    def custom_start_location(self):
        return self.nodes[0].location if self.nodes and self.nodes[0].kind == "custom_start" else None

    @property
    def custom_end_location(self):
        return self.nodes[-1].location if self.nodes and self.nodes[-1].kind == "custom_end" else None

    @property
    def is_complete(self):
        return bool(self.action_nodes) and all(
            index in self.visited_indices
            for index in range(len(self.action_nodes))
        )

    def next_action_index(self):
        if not self.action_nodes or self.is_complete:
            return None
        return next(
            (index for index in range(len(self.action_nodes)) if index not in self.visited_indices),
            None,
        )

    def active_leg_index(self):
        next_index = self.next_action_index()
        if next_index is None:
            return None
        path_index = self.action_node_path_indices[next_index]
        if path_index == 0:
            return None
        return path_index - 1

    def landmark_id_at(self, action_index):
        if action_index is None or action_index < 0 or action_index >= len(self.action_nodes):
            return None
        node = self.action_nodes[action_index]
        return node.landmark_id if node.is_landmark else None

    def next_landmark_id(self):
        return self.landmark_id_at(self.next_action_index())

    def visit(self, action_index):
        if action_index != self.next_action_index():
            raise ValueError("Can only visit the next route stop.")
        if action_index >= self.action_stop_count:
            raise ValueError("Route stop index is out of range.")
        self.visited_indices.add(action_index)

    def distance_to_next_m(self):
        active_index = self.active_leg_index()
        if active_index is None:
            return None
        for fallback_index, leg in enumerate(self.route_legs):
            if leg.get("from_index") == active_index or fallback_index == active_index:
                return leg.get("distance_m", 0)
        return None

    def progress_summary(self):
        active_index = self.active_leg_index()
        if self.is_complete:
            passed = sum(leg.get("distance_m", 0) for leg in self.route_legs)
            remaining = 0
        else:
            passed = sum(
                leg.get("distance_m", 0)
                for leg in self.route_legs
                if active_index is not None and leg.get("from_index", 0) < active_index
            )
            remaining = sum(
                leg.get("distance_m", 0)
                for leg in self.route_legs
                if active_index is None or leg.get("from_index", 0) >= active_index
            )
        total = passed + remaining
        return {
            "distance_to_next_m": self.distance_to_next_m(),
            "passed_distance_m": passed,
            "remaining_distance_m": remaining,
            "progress_percent": round((passed / total) * 100) if total else 0,
        }

    def to_store_dict(self) -> OptimizedTripStore:
        return {
            "visit_order": self.visit_order,
            "route_legs": self.route_legs,
            "custom_start_location": self.custom_start_location,
            "custom_end_location": self.custom_end_location,
            "total_distance_m": sum(leg.get("distance_m", 0) for leg in self.route_legs),
            "total_duration_s": sum(leg.get("duration_s", 0) for leg in self.route_legs),
        }


def _custom_location(point):
    if point and point.id == -1:
        return {"lat": point.lat, "lon": point.lon}
    return None


def _location_tuple(location):
    if not location:
        return None
    return location["lat"], location["lon"]


def _route_leg_dicts(route_point_count, route_result):
    return [
        {
            "from_index": index,
            "to_index": index + 1,
            "polyline": leg.polyline,
            "distance_m": leg.distance_m,
            "duration_s": leg.duration_s,
        }
        for index, leg in enumerate(route_result.legs)
        if index + 1 < route_point_count
    ]
