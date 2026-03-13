"""Particle swarm optimizer used by legacy advanced-service tests."""

from __future__ import annotations

import random
from typing import Any, Callable, Dict, List, Sequence, Tuple


class SwarmOptimizer:
    """Simple PSO implementation with async helpers."""

    def __init__(
        self,
        inertia: float = 0.7,
        cognitive: float = 1.4,
        social: float = 1.4,
    ) -> None:
        self.inertia = inertia
        self.cognitive = cognitive
        self.social = social

    async def optimize(
        self,
        objective_function: Callable[[Sequence[float]], float],
        dimensions: int,
        num_particles: int = 20,
        iterations: int = 50,
        bounds: List[Tuple[float, float]] | None = None,
    ) -> Dict[str, Any]:
        resolved_bounds = bounds or [(-1.0, 1.0)] * dimensions
        particles = self._initialize_particles(num_particles, dimensions, resolved_bounds)

        best_position = particles[0]["position"][:]
        best_score = float("inf")

        for _ in range(max(1, iterations)):
            scores = await self._evaluate_particles(objective_function, particles)

            for particle, score in zip(particles, scores):
                if score < particle["best_score"]:
                    particle["best_score"] = score
                    particle["best_position"] = particle["position"][:]

                if score < best_score:
                    best_score = score
                    best_position = particle["position"][:]

            for particle in particles:
                velocity = self._update_velocity(
                    particle=particle,
                    global_best_position=best_position,
                )
                particle["velocity"] = velocity
                particle["position"] = [
                    max(min(pos + vel, resolved_bounds[i][1]), resolved_bounds[i][0])
                    for i, (pos, vel) in enumerate(zip(particle["position"], velocity))
                ]

        return {
            "best_position": best_position,
            "best_score": best_score,
            "num_particles": num_particles,
            "iterations": iterations,
        }

    def _initialize_particles(
        self,
        num_particles: int,
        dimensions: int,
        bounds: List[Tuple[float, float]],
    ) -> List[Dict[str, Any]]:
        particles = []
        for _ in range(num_particles):
            position = [random.uniform(bounds[i][0], bounds[i][1]) for i in range(dimensions)]
            velocity = [random.uniform(-1.0, 1.0) for _ in range(dimensions)]
            particles.append(
                {
                    "position": position[:],
                    "velocity": velocity,
                    "best_position": position[:],
                    "best_score": float("inf"),
                }
            )
        return particles

    def _update_velocity(
        self,
        particle: Dict[str, Any],
        global_best_position: Sequence[float],
    ) -> List[float]:
        updated = []
        for i, current_velocity in enumerate(particle["velocity"]):
            r1 = random.random()
            r2 = random.random()
            cognitive_term = self.cognitive * r1 * (particle["best_position"][i] - particle["position"][i])
            social_term = self.social * r2 * (global_best_position[i] - particle["position"][i])
            new_velocity = (self.inertia * current_velocity) + cognitive_term + social_term
            updated.append(new_velocity)
        return updated

    async def _evaluate_particles(
        self,
        objective_function: Callable[[Sequence[float]], float],
        particles: List[Dict[str, Any]],
    ) -> List[float]:
        return [float(objective_function(particle["position"])) for particle in particles]


swarm_optimizer = SwarmOptimizer()

