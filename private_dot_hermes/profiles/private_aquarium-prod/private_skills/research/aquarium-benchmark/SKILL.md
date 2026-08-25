---
name: aquarium-benchmark
description: "Build AAA 3D aquarium sim: Three.js r128, TDD, self-repair."
version: 1.0.0
author: imshubhamsocial, Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [threejs, webgl, benchmark, aquarium, simulation, tdd, physics]
    related_skills: [systematic-debugging, test-driven-development]
---

# AAA Interactive 3D WebGL Aquarium Benchmark

## Role

You are a Principal 3D Creative Engineer and Three.js Specialist executing a
timed benchmark. Build a **single-file, production-grade** interactive 3D
WebGL Aquarium Simulation. Your output MUST be a complete, valid HTML file
written directly to disk using the `write_file` tool.

## Output Target

Write the complete HTML file to:
`/var/home/imshubhamsocial/Projects/Workspace/Personal/LLMs/aquarium-benchmark-production/build_preview.html`

The file MUST start with `<!DOCTYPE html>` and end with `</html>`.
ALL JavaScript MUST be inlined inside a single `<script>` tag. NO external
relative src files — they break under `file://` CORS policy.

## CDN Tags (exact, do not change)

```html
<script src="https://unpkg.com/three@0.128.0/build/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
```

## Global Variable Contracts (mandatory — TDD checks these by name)

```js
let scene, camera, renderer, controls, ball, ballVel, isDraggingBall = false;
let fishes = [], seaweeds = [], bubbles = [];
const TANK = { w: 36, h: 22, d: 24 };
const WATER_Y = 6;
```

## Section 1 — Scene, Atmosphere & Shadows

- `scene.background = new THREE.Color(0x062846)` + `THREE.FogExp2(0x062846, 0.015)`
- `renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;`
- Ambient Light: `0x225588`, intensity `1.5`
- Directional sunlight `0xaae5ff`, intensity `2.5` at `(15, 30, 20)`:
  - `castShadow = true`, mapSize `2048×2048`, `bias = -0.001`
- Bottom Cyan Point: `0x00d2ff`, intensity `1.5` at tank center bottom
- Glass tank: `BoxGeometry(TANK.w, TANK.h, TANK.d)` with `MeshPhysicalMaterial`
  `{ color: 0x99ddff, transparent: true, opacity: 0.15, roughness: 0.05, transmission: 0.9, depthWrite: false, side: THREE.DoubleSide }`
- Cyan metallic border: `EdgesGeometry` + `LineSegments` (`0x00ffff`)
- Sand floor: `PlaneGeometry(TANK.w-0.5, TANK.d-0.5)` `MeshStandardMaterial { color: 0xd9b36c, roughness: 0.9 }` at `y = -TANK.h/2 + 0.1`, `receiveShadow = true`
- Camera: `PerspectiveCamera(55, innerWidth/innerHeight, 0.1, 1000)` at `(0, 14, 42)`, target `(0,0,0)`

## Section 2 — Spring-Mass Water Surface

- `PlaneGeometry(TANK.w-0.2, TANK.d-0.2, 48, 48)` assigned to global `water` at `y = WATER_Y`
- `MeshPhysicalMaterial { color: 0x0088cc, transparent: true, opacity: 0.55, roughness: 0.1, transmission: 0.8, depthWrite: false, side: THREE.DoubleSide }`
- Wave grid: `gridCount = 49*49 = 2401` vertices, `Float32Array` for `heights` and `velocities`
- Physics: tension `k=0.025`, damping `d=0.96`, 4-neighbour spring `c=0.05`
- Per-frame: `water.geometry.attributes.position.setZ(i, heights[i]); water.geometry.computeVertexNormals();`
- `triggerRipple(x, z, strength)` function sets adjacent grid heights
- Right-click: raycasts water plane, bounds `|x|<17, |z|<11`, calls `triggerRipple(hit.x, hit.z, 1.5)`
- `window.addEventListener('contextmenu', e => e.preventDefault());`
- Ball splash: `triggerRipple(ball.position.x, ball.position.z, Math.abs(ballVel.y) * 0.4)` on water entry
- Fish reaction: perturb nearby fish `d < 5.0` away from ripple epicenter

## Section 3 — Fish Class (exact anatomy)

Instantiate **15 Fish** objects pushed into global `fishes` array, each added to `scene`.

```js
class Fish {
  constructor() {
    this.group = new THREE.Group();
    // Body: elongated ellipsoid
    const bodyGeo = new THREE.SphereGeometry(1.0, 16, 16);
    bodyGeo.scale(0.5, 0.7, 1.8);
    this.body = new THREE.Mesh(bodyGeo, bodyMat);
    this.group.add(this.body);
    // Caudal tail fin
    const tailGeo = new THREE.ConeGeometry(0.6, 1.2, 3);
    this.tail = new THREE.Mesh(tailGeo, finMat);
    this.tail.scale.set(0.15, 1.2, 1.0);
    this.tail.rotation.x = Math.PI / 2;
    this.tail.position.z = -1.8;
    this.group.add(this.tail);
    // Dorsal fin
    const dorsalGeo = new THREE.ConeGeometry(0.4, 0.8, 3);
    this.dorsal = new THREE.Mesh(dorsalGeo, finMat);
    this.dorsal.scale.set(0.1, 1.0, 1.0);
    this.dorsal.position.set(0, 0.7, -0.2);
    this.group.add(this.dorsal);
    // Symmetrical eyes
    [-0.38, 0.38].forEach(sx => {
      const eye = new THREE.Mesh(new THREE.SphereGeometry(0.12, 8, 8), eyeMat);
      eye.position.set(sx, 0.15, 0.9);
      this.group.add(eye);
    });
    this.group.castShadow = true;
    this.vel = new THREE.Vector3(...); // random init
    this.phase = Math.random() * Math.PI * 2;
  }
  update(time, fishes, ball) {
    // Craig Reynolds Boids: Separation + Alignment + Cohesion
    // Wall margin = 4.0 for smooth boundary avoidance
    // Ball fleeing when distance < 6.0
    // Heading: group.rotation.y = THREE.MathUtils.lerp(group.rotation.y, Math.atan2(-vel.x, -vel.z) + Math.PI, 0.08)
    // Tail wag: this.tail.rotation.y = Math.sin(time * 12 + this.phase) * 0.45
    // castShadow = true on body, tail, dorsal
  }
}
```

## Section 4 — Seaweed (18 plants)

- 18 `PlaneGeometry(0.8, height, 1, 8)` vertical planes, `THREE.DoubleSide`, colour `0x118833`
- Anchored to sand floor, sway: `mesh.rotation.z = Math.sin(time * 1.5 + offset) * 0.18`
- `castShadow = true`

## Section 5 — Buoyant Ball & HUD

- Yellow `SphereGeometry(1.8, 32, 32)`, assigned to global `ball`, `castShadow = true`
- Physics (per animate frame):
  - `ballVel = new THREE.Vector3()`; gravity `gy = -16.0`
  - Submerged when `ball.position.y < WATER_Y + 1.8`
  - Buoyancy: `F = Math.min(submergedFrac, 1.2) * 28.0`; drag in water `*= 0.94`; gravity in air
  - Bounce on tank walls with reflection, ceiling clamp `y <= WATER_Y + 4`
- Left-click drag: raycaster across camera projection plane, fling on release with velocity
  - `isDraggingBall` flag, `pointerdown/pointermove/pointerup` listeners
- Frosted-glass HUD top-left: `backdrop-filter: blur(10px)`, instructions

## Section 6 — animate() Loop

```js
function animate() {
  requestAnimationFrame(animate);
  const time = performance.now() * 0.001;
  // 1. Update spring-mass wave grid
  // 2. Update ball physics + ball→water ripple trigger
  // 3. fishes.forEach(f => f.update(time, fishes, ball))
  // 4. Update seaweed sway
  // 5. Update bubbles (rise from seabed y=-TANK.h/2 to WATER_Y, reset on exit)
  // 6. controls.update(); renderer.render(scene, camera);
}
```

60 rising bubbles in global `bubbles` array: `SphereGeometry(0.12, 6, 6)`, rise from seabed
to `WATER_Y` with gentle lateral drift, reset position when they exit.

`window.addEventListener('resize', ...)` for responsive canvas.

## TDD Gate — 7 Contracts (run AFTER writing the file)

Run via terminal tool:

```bash
python3 \
  tests/test_simulation_contracts.py \
  build_preview.html \
  screenshots/pro_build_snapshot.png
```

Contracts that must all PASS:
1. **Static Syntax** — Node.js `new Function(js)` parse passes
2. **WebGL Canvas Mounted** — `<canvas>` exists in DOM
3. **Zero Runtime Errors** — no JS exceptions at runtime
4. **Fish Count ≥ 14** — `fishes.length >= 14`
5. **Seaweed Count ≥ 16** — `seaweeds.length >= 16`
6. **Bubbles Count ≥ 50** — `bubbles.length >= 50`
7. **Ball Exists** — `typeof ball !== 'undefined' && ball !== null`

## Self-Repair Protocol

If any contract fails:
1. Read the exact error message from TDD output
2. Read the current `build_preview.html` using `read_file`
3. Identify the precise failing scope/variable/logic
4. Write the corrected complete file back to `build_preview.html`
5. Re-run TDD gate
6. Repeat until all 7 contracts pass

Do NOT patch partial snippets. Always rewrite the complete file.

## When to Use This Skill

Activate when the user requests the aquarium benchmark run, says "Start", or
asks to generate / repair the aquarium simulation.
