from dash import html
import dash_leaflet as dl


def build_access_connector_polylines(landmarks, id_prefix="access-connector"):
    connectors = []
    seen_landmark_ids = set()
    for landmark in landmarks:
        if not landmark.has_access_point or landmark.id in seen_landmark_ids:
            continue
        seen_landmark_ids.add(landmark.id)
        connectors.append(
            html.Div(
                dl.Polyline(
                    id=f"{id_prefix}-{landmark.id}",
                    positions=[
                        [landmark.access_point["lat"], landmark.access_point["lon"]],
                        [landmark.lat, landmark.lon],
                    ],
                    color="#4b5563",
                    weight=5,
                    opacity=0.95,
                    dashArray="8 8",
                )
            )
        )
    return connectors
