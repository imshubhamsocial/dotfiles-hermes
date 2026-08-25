# Integrator Module (src/physics/integrator.py)
from src.physics.vector3 import Vector3

class EulerIntegrator:
    def __init__(self, gravity: float = 9.81):
        self.gravity = Vector3(0.0, -gravity, 0.0)

    def step(self, position: Vector3, velocity: Vector3, dt: float) -> tuple[Vector3, Vector3]:
        # Velocity update
        new_velocity = velocity.add(self.gravity.scale(dt))
        # Position update
        new_position = position.add(new_velocity.scale(dt))
        return new_position, new_velocity
