import math
from typing import List, Optional

from services.landmark_registry import Landmark


def haversine(a: Landmark, b: Landmark) -> float:
    """
    Calculate the great-circle distance between two points on the Earth using Haversine formula.
    Returns distance in kilometers.
    """
    R = 6371  # Earth radius in km

    a_lat, a_lon = a.routing_coordinates()
    b_lat, b_lon = b.routing_coordinates()

    dlat = math.radians(b_lat - a_lat)
    dlon = math.radians(b_lon - a_lon)

    sa = math.sin(dlat / 2)
    sb = math.sin(dlon / 2)

    h = sa * sa + math.cos(math.radians(a_lat)) * math.cos(math.radians(b_lat)) * sb * sb

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
        # External start point (e.g. user's current location) is not a destination.
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
        # External end point (e.g. user's current location) is not a destination.
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


def route_distance(route: List[Landmark]) -> float:
    return sum(haversine(route[i], route[i + 1]) for i in range(len(route) - 1))


def two_opt_by_distance(route: List[Landmark], fix_start=True, fix_end=False) -> List[Landmark]:
    """
    2-opt variant for open routes. It recomputes total route distance for each
    candidate reversal, which lets automatic routes improve their first stop.
    """
    route = route.copy()
    improved = True
    epsilon = 1e-9

    while improved:
        improved = False
        best_distance = route_distance(route)
        first_index = 1 if fix_start else 0
        last_index = len(route) - 2 if fix_end else len(route) - 1

        for i in range(first_index, last_index):
            for j in range(i + 1, last_index + 1):
                if not fix_start and not fix_end and i == 0 and j == len(route) - 1:
                    continue

                candidate = route[:i] + list(reversed(route[i:j + 1])) + route[j + 1:]
                candidate_distance = route_distance(candidate)
                if candidate_distance + epsilon < best_distance:
                    route = candidate
                    best_distance = candidate_distance
                    improved = True
                    break
            if improved:
                break

    return route


