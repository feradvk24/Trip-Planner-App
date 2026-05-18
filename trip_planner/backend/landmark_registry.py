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

    def routing_coordinates(self):
        if (
            self.access_point
            and self.access_point.get("lat") is not None
            and self.access_point.get("lon") is not None
        ):
            return self.access_point["lat"], self.access_point["lon"]
        return self.lat, self.lon

    def __repr__(self):
        return f"Landmark(id={self.id}, name='{self.name}', location='{self.location}', lat={self.lat}, lon={self.lon})"

class LandmarkRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LandmarkRegistry, cls).__new__(cls)
            cls._instance._landmarks = {}
        return cls._instance

    @classmethod
    def from_database(cls):
        registry = cls()
        registry.load_from_database()
        return registry

    def load_from_database(self):
        from backend.database import SessionLocal
        from backend.models import Landmark as LandmarkModel

        db = SessionLocal()
        try:
            db_landmarks = db.query(LandmarkModel).all()
            landmarks = [
                Landmark(
                    id=row.id,
                    name=row.name,
                    location=row.location or "Location",
                    lat=row.latitude,
                    lon=row.longitude,
                    link=row.link or "#",
                    access_point=row.access_point,
                )
                for row in db_landmarks
            ]
        finally:
            db.close()

        self._landmarks = {landmark.id: landmark for landmark in landmarks}
        return self

    def get_landmark(self, landmark_id):
        return self._landmarks.get(landmark_id)

    def get_landmarks(self, ids):
        return [self._landmarks[i] for i in ids if i in self._landmarks]
    
    @property
    def landmarks(self):
        return list(self._landmarks.values())
