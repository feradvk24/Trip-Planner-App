from dataclasses import dataclass

@dataclass
class Landmark:
    id: int
    name: str
    location: str
    lat: float
    lon: float
    link: str = "#" 

    def __repr__(self):
        return f"Landmark(id={self.id}, name='{self.name}', location='{self.location}', lat={self.lat}, lon={self.lon})"

class LandmarkRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LandmarkRegistry, cls).__new__(cls)
            cls._instance._landmarks = {}
        return cls._instance

    def register_landmarks(self, landmark_list):
        self._landmarks = {l.id: l for l in landmark_list}

    def get_landmark(self, landmark_id):
        return self._landmarks.get(landmark_id)

    def get_landmarks(self, ids):
        return [self._landmarks[i] for i in ids if i in self._landmarks]
    
    @property
    def landmarks(self):
        return list(self._landmarks.values())