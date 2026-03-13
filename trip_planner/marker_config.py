class Landmark:
    def __init__(self, id, name, location, lat, lon, link="#"):
        self.id = id
        self.name = name
        self.location = location
        self.lat = lat
        self.lon = lon
        self.link = link

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