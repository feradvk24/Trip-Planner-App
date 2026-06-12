from dataclasses import dataclass
from typing import Optional


@dataclass
class Landmark:
    id: int
    name: str
    location: str
    lat: float
    lon: float
    link: str = "#"
    access_point: Optional[dict] = None

    @property
    def has_access_point(self):
        return (
            isinstance(self.access_point, dict)
            and self.access_point.get("lat") is not None
            and self.access_point.get("lon") is not None
        )

    def routing_coordinates(self):
        if self.has_access_point:
            return self.access_point["lat"], self.access_point["lon"]
        return self.lat, self.lon

    def __repr__(self):
        return f"Landmark(id={self.id}, name='{self.name}', location='{self.location}', lat={self.lat}, lon={self.lon})"


class LandmarkRegistry:
    _instance = None

    def __init__(self, landmarks=None):
        self._landmarks = {
            landmark.id: landmark
            for landmark in (landmarks or [])
        }

    @classmethod
    def from_records(cls, landmark_records):
        return cls([
            Landmark(
                id=row["id"],
                name=row["name"],
                location=row["location"],
                lat=row["lat"],
                lon=row["lon"],
                link=row["link"],
                access_point=row["access_point"],
            )
            for row in landmark_records
        ])

    @classmethod
    def get_landmarks(cls):
        if cls._instance is None:
            from trip_planner.backend.db.crud import get_landmarks

            cls._instance = cls.from_records(get_landmarks())
        return cls._instance

    def get_landmark(self, landmark_id):
        return self._landmarks.get(landmark_id)

    def landmarks_by_ids(self, ids):
        return [self._landmarks[i] for i in ids if i in self._landmarks]

    @property
    def landmarks(self):
        return list(self._landmarks.values())
