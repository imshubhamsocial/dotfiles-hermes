# Vector3 Interface Module (src/physics/vector3.py)
import math

class Vector3:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def magnitude(self) -> float:
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def normalize(self) -> 'Vector3':
        m = self.magnitude()
        if m == 0:
            return Vector3(0, 0, 0)
        return Vector3(self.x / m, self.y / m, self.z / m)

    def add(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def scale(self, factor: float) -> 'Vector3':
        return Vector3(self.x * factor, self.y * factor, self.z * factor)

    def euclidean_dist(self, v2: 'Vector3') -> float:
        dx = v2.x - self.x
        dy = v2.y - self.y
        dz = v2.z - self.z
        return math.sqrt(dx*dx + dy*dy + dz*dz)

    def dot(self, other: 'Vector3') -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.y * other.z - self.z * other.y, self.z * other.x - self.x * other.z, self.x * other.y - self.y * other.x)
