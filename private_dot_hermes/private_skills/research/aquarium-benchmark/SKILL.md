---
name: aquarium-benchmark
category: research
description: Build AAA 3D WebGL aquarium with boids fish, spring-mass water, and physics.
---

# AAA 3D Aquarium Simulation

**Trigger:** Build a complete AAA-quality 3D WebGL aquarium simulation with boids fish, spring-mass water surface, and interactive physics.

**Context:** Create a self-contained HTML file with WebGL/Three.js aquarium simulation. Must be runnable standalone without external assets.

**Steps:**

1. **Set up scene and renderer**
   - Three.js PerspectiveCamera
   - WebGLRenderer with shadow map enabled
   - OrbitControls for camera
   - Ambient light + directional light + point light
   - Glass tank (MeshPhysicalMaterial with transmission)
   - Sand floor

2. **Water surface (double-buffered spring-mass)**
   - PlaneGeometry 49×49 vertices
   - Float32Array heights and velocities for performance
   - Spring-mass: neighbors average height, spring force, damping
   - computeVertexNormals each frame
   - MeshPhysicalMaterial with transmission and roughness

3. **Fish (15 instances, boids physics)**
   - Each fish: unique material (no shared references)
   - Boids: separation, alignment, cohesion with tuned weights
   - Bank turn steering (yaw toward velocity)
   - Tail/body undulation animation
   - Flee from ball when close
   - Bounce off glass walls
   - Trigger ripple on surface

4. **Seaweeds (28 instances)**
   - PlaneGeometry with randomized height
   - Sway animation tied to water surface
   - Physical material with transmission

5. **Bubbles (60 instances)**
   - SphereGeometry with transmission material
   - Rise animation with opacity fade
   - Respawn at bottom, pop at surface

6. **Buoyant ball**
   - SphereGeometry with physical material
   - Archimedes buoyancy: buoyant force ∝ submerged depth
   - Quadratic drag: velocity decays when submerged
   - Bounce off tank walls with energy loss
   - Ripple trigger on impact

7. **Interaction**
   - Right-click on water → ripple
   - Drag ball → throw with physics-based trajectory

8. **Optimization**
   - MathUtils.lerp for smooth interpolation
   - Float32Array for water grid (memory efficient)
   - Capped devicePixelRatio at 2x
   - Use `needsUpdate = true` + `computeVertexNormals()` for water

**Output:** Single `build_preview.html` file, runnable in any modern browser with WebGL2.

**Format:** Complete self-contained HTML with embedded CSS and JS.