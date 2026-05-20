# Black Hole Simulation

A 2D gravitational physics simulation of an accretion disk around a stellar-mass black hole, built from scratch in Python.

![preview](preview.png)

## Physics
- Newtonian gravity: F = G·m₁·m₂ / r²
- RK4 integration for energy conservation
- Schwarzschild radius: rs = 2GM/c²
- 150 particles with elliptical orbits colored by speed

## Run it
pip install matplotlib numpy
py -3.12 simulation.py