# 🏛️ Master Architectural Specification (PLAN.md)
## Project: AAA Interactive 3D WebGL Physics, Fluid & Boids Ecosystem

---

### 1. Scene Graph Hierarchy, Atmosphere & 3-Point Studio Lighting
- **Background & Atmosphere**: `scene.background = new THREE.Color(0x0d1a26)` with matching exponential fog `THREE.FogExp2(0x0d1a26, 0.006)`.
- **Shadow-Enabled Lighting Architecture**:
  - `renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap; renderer.toneMapping = THREE.ACESFilmicToneMapping;`
  - Key Light: `0xffeedd`, intensity `2.2`, positioned at `(5, 35, 10)`, `shadow.mapSize.set(2048, 2048)`, `shadow.bias = -0.0008`.
  - Fill Light: `0x88aacc`, intensity `0.6`, positioned at `(-15, 10, 25)`.
  - Rim Light: `0xffcc88`, intensity `0.35`, positioned at `(10, 20, -20)`.
  - Ambient & Hemisphere: `AmbientLight(0x445566, 0.5)` + `HemisphereLight(0x6688bb, 0xc4a050, 0.3)`.
  - Animated Caustic Point Light: `0x88ddff`, intensity `0.4 + 0.2*sin(1.5t)` drifting in 3D sinusoidal orbits.
- **Glass Tank, Depth Box, Sand Floor & Pebbles**:
  - Tank dimensions: `TANK = { w: 36, h: 22, d: 24 }`, `WATER_Y = 6`.
  - Borosilicate Glass: `MeshPhysicalMaterial({ color: 0xe0f0e8, transparent: true, opacity: 0.06, roughness: 0.02, transmission: 0.95, ior: 1.52, thickness: 0.8, clearcoat: 1.0, depthWrite: false, side: THREE.DoubleSide })`.
  - Edge Highlight: `LineSegments(EdgesGeometry(tankGeo), LineBasicMaterial({ color: 0x99ccdd, transparent: true, opacity: 0.35 }))`.
  - Inverted Depth Volume: `BoxGeometry(35.4, 21.5, 23.4)` at $y = -0.25$ with `side: THREE.BackSide`, `opacity: 0.12`.
  - Sand Bed & 40 Pebbles: Sand plane at $y = -10.98$ with `receiveShadow = true`, plus 40 randomly scaled/colored pebbles with shadow casting/receiving.

---

### 2. 81×81 Double-Buffered Shallow-Water Wave Solver with Volume Conservation
- **Realistic Water Surface Mesh**:
  - `PlaneGeometry(35.6, 23.6, 80, 80)` rotated $-90^\circ$ on X at $y = \text{WATER\_Y} = 6$.
  - Material: `MeshPhysicalMaterial({ color: 0x1a7088, transparent: true, opacity: 0.5, roughness: 0.05, transmission: 0.75, ior: 1.333, thickness: 2.0, depthWrite: false, side: THREE.DoubleSide })`.
- **Wave Grid Numerical Equation**:
  - Double-buffered `hA`, `hB`, `vel` Float32 arrays of size $81 \times 81 = 6561$.
  - `lap = -4*hA[k] + hA[i-1,j] + hA[i+1,j] + hA[i,j-1] + hA[i,j+1]`.
  - `vel[k] = (vel[k] + lap * 0.22) * 0.996`, `hB[k] = hA[k] + vel[k]`.
  - Volume Conservation: Mean height subtracted on every step (`mean = sum(hB)/N; hB[k] -= mean`).
  - Vertex update: `pos.setZ(k, hA[k]); water.geometry.computeVertexNormals()`.
- **Gaussian Ripple Injection**:
  - Signed velocity impulse: $\Delta \text{vel} += \exp(-d^2 / 3.5) \times \text{strength}$.

---

### 3. Anatomical Multi-Mesh Boid Fish & 28 Seaweed Flora
- **15 Tropical Boid Fish (`class Fish`)**:
  - 8 tropical colors (`[0xe8443a, 0x1a9fcc, 0xf0a020, 0x2eb866, 0x8844cc, 0xee5588, 0x18ccaa, 0x4488ff]`).
  - Body ellipsoid `SphereGeometry(0.85, 14, 14)` scaled $(0.47, 0.67, 1.75)$.
  - 3-sided tail fin cone at $z = -1.75$ with dynamic wag frequency $8.0 + 50.0 \times \|\vec{v}\|$.
  - Dorsal fin cone at $(0, 0.67, -0.19)$.
  - Symmetrical pupil/eye spheres at $(\pm 0.38, 0.15, 0.9)$.
  - Flocking: Separation ($0.018$), Alignment ($0.007$), Cohesion ($0.005$), Ball avoidance ($0.07$), Velocity clamp $[0.06, 0.18]$, Mid-depth centering pull ($y = -2.25$).
  - Yaw/Pitch/Roll banking into turns, surface ripple emission when $y > 2.5$.
- **28 Segmented Swaying Seaweed Plants**:
  - 28 double-sided planes anchored on sandbed floor ($y = -10.9$) with dual-harmonic sway.
- **60 Translucent Rising Bubbles**:
  - Translucent spheres rising with sinusoidal drift, popping at $y \ge 5.8$ to inject surface ripples.

---

### 4. Interactive Buoyancy Ball & Hydrodynamic Coupling
- Red clearcoat sphere `SphereGeometry(1.8, 32, 32)` with gravity ($G = 22.0$).
- Archimedes buoyancy force ($G \cdot \text{frac} \cdot 2.0$), quadratic viscous drag ($C_d = 3.0$), wave gradient lateral drift.
- `stampBallIntoWater()`: Depresses water surface under ball with Gaussian kernel, raising surrounding water via volume conservation.
- Raycaster Pointer Interaction: Dragging ball along camera projection plane with velocity tracking and ripple trails; clicking water injects ripples and scatters nearby fish.
