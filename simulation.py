import math
import time
import random
import matplotlib.pyplot as plt

# Vector class
class Vec2: 
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    def __add__(self, other): return Vec2(self.x + other.x, self.y + other.y)
    def __sub__(self, other): return Vec2(self.x - other.x, self.y - other.y)
    def __mul__(self, scalar): return Vec2(self.x * scalar, self.y * scalar)
    def __truediv__(self, scalar): return Vec2(self.x / scalar, self.y / scalar)
    def __repr__(self):              return f"Vec2({self.x:.3f}, {self.y:.3f})"

    def magnitude(self): return math.sqrt(self.x**2 + self.y**2)
    def normalized(self): m = self.magnitude(); return Vec2(self.x/m, self.y/m)
    def dot(self, other): return self.x*other.x + self.y*other.y


# Body Class
class Body:
    def __init__(self, mass: float, pos: Vec2, vel: Vec2, is_black_hole: bool = False):
        self.mass = mass
        self.pos = pos
        self.vel = vel
        self.acc = Vec2(0, 0)   # reset each frame
        self.is_black_hole = is_black_hole
    
    @property
    def event_horizon(self):
        # Only meaningful if this body is a black hole
        # Returns 0 for normal bodies
        if self.is_black_hole:
            return schwarzchild_radius(self.mass)
        return 0.0
    
    def update(self, dt: float, force_fn):
        # force_fn is a function that takes position and returns acceleration
        # This lets RK4 sample the force at different positions
        def acc(pos): return force_fn(pos) / self.mass
        k1v = acc(self.pos)
        k1x = self.vel
        k2v = acc(self.pos + k1x * (dt/2))
        k2x = self.vel + k1v * (dt/2)
        k3v = acc(self.pos + k2x * (dt/2))
        k3x = self.vel + k2v * (dt/2)
        k4v = acc(self.pos + k3x * dt)
        k4x = self.vel + k3v * dt
        self.vel = self.vel + (k1v + k2v*2 + k3v*2 + k4v) * (dt/6)
        self.pos = self.pos + (k1x + k2x*2 + k3x*2 + k4x) * (dt/6)

# Gravity between two bodies: G*m1*m2/r^2
G = 6.674e-11
def gravitational_force(b1: Body, b2: Body) -> Vec2:
    delta = b2.pos - b1.pos
    r = delta.magnitude()
    if r < 1e-6: return Vec2(0, 0)

    magnitude = G * b1.mass * b2.mass / (r**2)
    direction = delta.normalized()
    return direction * magnitude    # force vector on b1

def kinetic_energy(body: Body) -> float:
    v = body.vel.magnitude()
    return 0.5 * body.mass * v**2
def potential_energy(b1: Body, b2: Body) -> float:
    r = (b2.pos - b1.pos).magnitude()
    return -G * b1.mass * b2.mass / r

c = 3e8
def schwarzchild_radius(mass: float) -> float:
    # radius = 2GM/c^2
    rs = (2 * G * mass) / c**2
    return rs

# Seeing if Event Horizon (point of no return) has been reached
def is_captured(body: Body, black_hole: Body) -> bool:
    r = (body.pos - black_hole.pos).magnitude()
    rs = schwarzchild_radius(black_hole.mass)
    return r <= rs  # if closer than event horion --> captured




def run_simulation(bodies: list[Body], dt=0.1, steps=1000):
    history = [[] for _ in bodies]
    captured = [False] * len(bodies)  # tracks which bodies are captured

    for step in range(steps):
        # --- Force collection (same as before) ---
        def make_force_fn(body_index):
            def force_fn(pos):
                total = Vec2(0, 0)
                for j, b2 in enumerate(bodies):
                    if j == body_index: continue
                    if captured[j]: continue

                    # NEW: skip particle-to-particle forces (too small to matter)
                    # Only calculate force if b2 is the black hole
                    if not b2.is_black_hole: continue

                    delta = b2.pos - pos
                    r = delta.magnitude()
                    if r < 1e-6: continue
                    mag = G * bodies[body_index].mass * b2.mass / (r**2)
                    total = total + delta.normalized() * mag
                return total
            return force_fn

        # --- Update positions ---
        for i, body in enumerate(bodies):
            if captured[i]: continue  # skip captured bodies
            body.update(dt, make_force_fn(i))
            history[i].append((body.pos.x, body.pos.y, body.vel.magnitude()))

        # --- Event horizon check ---
        # For every non-black-hole body, check against every black hole
        for i, body in enumerate(bodies):
            if captured[i] or body.is_black_hole: continue
            for bh in bodies:
                if not bh.is_black_hole: continue
                r = (body.pos - bh.pos).magnitude()
                if r <= bh.event_horizon:
                    captured[i] = True
                    print(f"Step {step}: Body {i} captured by black hole!")

        # --- Energy print ---
        if step % 1000 == 0:
            active = [b for i,b in enumerate(bodies) if not captured[i]]
            if len(active) >= 2:
                KE = sum(kinetic_energy(b) for b in active)
                PE = potential_energy(active[0], active[1])
                print(f"Step {step:6d} | Total Energy: {KE+PE:.6e}")

    # --- Plot all trajectories ---
    import matplotlib
    cmap = matplotlib.colormaps['plasma']
    plt.figure(figsize=(11, 8))


    # Find speed range for color normalization
    all_speeds = []
    for i, traj in enumerate(history):
        if bodies[i].is_black_hole: continue
        for x, y, speed in traj:
            all_speeds.append(speed)

    max_speed = max(all_speeds) if all_speeds else 1.0
    min_speed = min(all_speeds) if all_speeds else 0.0

    for i, traj in enumerate(history):
        if len(traj) == 0: continue

        if bodies[i].is_black_hole:
            plt.plot(0, 0, 'o', color='white', markersize=10, zorder=10)
            continue

        xs     = [p[0] for p in traj]
        ys     = [p[1] for p in traj]
        speeds = [p[2] for p in traj]

        # Color this trail by its average speed
        avg_speed = sum(speeds) / len(speeds)
        norm_speed = norm_speed = 0.4 + 0.6 * (avg_speed - min_speed) / (max_speed - min_speed)
        color = cmap(norm_speed)

        plt.plot(xs, ys, color=color, linewidth=0.4, alpha=0.7)

    # Event horizon glow ring
    glow_r = 2.2e11 * 0.012
    circle = plt.Circle((0, 0), glow_r, color='orangered',
                         fill=False, linewidth=2, label='Event Horizon')
    plt.gca().add_patch(circle)

    plt.gca().set_facecolor('black')
    plt.gcf().set_facecolor('black')
    plt.title("Black Hole Simulation — Accretion Disk", color='white')
    plt.axis('equal')
    plt.tight_layout()

    # --- Info panel ---
    simulated_years = (10000 * 3600) / (365.25 * 24 * 3600)
    info_lines = [
        "BLACK HOLE SIMULATION",
        "─" * 26,
        f"BH Mass:       10 M☉",
        f"Event horizon: {schwarzchild_radius(bodies[0].mass)/1000:.1f} km",
        f"Particles:     150",
        f"Disk range:    0.27 – 1.47 AU",
        f"Timestep:      1 hour",
        f"Simulated:     {simulated_years:.1f} years",
        "─" * 26,
        "Colour = orbital speed",
        "pink/yellow = fast (inner)",
        "purple = slow (outer)",
    ]

    info_text = "\n".join(info_lines)

    plt.gcf().text(
        0.02, 0.5,           # x, y in figure coordinates (0–1)
        info_text,
        color     = 'white',
        fontsize  = 9,
        fontfamily= 'monospace',
        va        = 'center',
        bbox      = dict(
            boxstyle    = 'round',
            facecolor   = '#111111',
            edgecolor   = 'orangered',
            alpha       = 0.8,
            pad         = 0.8
        )
    )

    plt.show()





if __name__ == "__main__":
    random.seed(42)

    # Black Hole: 10x sun mass
    black_hole = Body(
        mass = 1.989e31, # 10 solar masses
        pos = Vec2(0, 0),
        vel = Vec2(0, 0),
        is_black_hole = True
    )

    rs = schwarzchild_radius(black_hole.mass)
    print(f"Event horizon radius: {rs:.2f} meters ({rs/1000:.2f} km)")

    R_INNER = 0.4e11    # inner edge of disk
    R_OUTER = 2.2e11    # outer edge of disk

    bodies = [black_hole]

    for i in range(150):
        angle = random.uniform(0, 2 * math.pi)
        radius = random.uniform(R_INNER, R_OUTER)
        pos = Vec2(math.cos(angle)*radius, math.sin(angle)*radius)
        # Circular orbit speed at this radius: v = sqrt(G*M/r)
        # Use 70-95% of it so orbits are elliptical and slowly spiral in
        v_circ = math.sqrt(G * black_hole.mass / radius)
        speed  = v_circ * random.uniform(0.70, 0.95)

        vel = Vec2(-math.sin(angle) * speed, math.cos(angle) * speed)
        bodies.append(Body(mass=1e20, pos=pos, vel=vel))

    run_simulation(bodies, dt=3600, steps=10000)







