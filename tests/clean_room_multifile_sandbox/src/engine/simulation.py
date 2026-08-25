# Engine Coordinator Module (src/engine/simulation.py)
from src.physics.vector3 import Vector3
from src.physics.integrator import EulerIntegrator

class ParticleSimulation:
    def __init__(self, count: int = 10):
        self.integrator = EulerIntegrator(gravity=9.81)
        self.particles = [{"pos": Vector3(0, 10, 0), "vel": Vector3(1, 0, 0)} for _ in range(count)]

    def tick(self, dt: float = 0.016):
        for p in self.particles:
            p["pos"], p["vel"] = self.integrator.step(p["pos"], p["vel"], dt)

    def get_mean_altitude(self) -> float:
        if not self.particles:
            return 0.0
        return sum(p["pos"].y for p in self.particles) / len(self.particles)

    def get_total_kinetic_energy(self) -> float:
        return 0.5 * sum(p["vel"].dot(p["vel"]) for p in self.particles)

    def get_total_momentum(self) -> float:
        return sum(p["vel"].magnitude() for p in self.particles)

    def get_particle_count(self) -> int:
        return len(self.particles)
