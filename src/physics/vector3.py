from __future__ import annotations


class Vector3:
    """3D Vector class with arithmetic operations."""

    def __init__(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z

    def cross(self, other: 'Vector3') -> 'Vector3':
        """Return the cross product of this vector with another."""
        return Vector3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )
