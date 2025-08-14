import math
import numpy as np

LAT_STEPS = 96  # Increased for better sphere resolution
LON_STEPS = 192  # Increased for better sphere resolution
BASE_RADIUS = 3.0
POINT_BASE_SIZE = 2.8  # Slightly smaller for more points

class SphereModel:
    def __init__(self):
        verts, norms, phases, sens, sizes = [], [], [], [], []
        for i in range(LAT_STEPS + 1):
            theta = math.pi * i / LAT_STEPS
            for j in range(LON_STEPS):
                phi = 2 * math.pi * j / LON_STEPS
                x = math.sin(theta) * math.cos(phi)
                y = math.cos(theta)
                z = math.sin(theta) * math.sin(phi)
                verts.append((x * BASE_RADIUS, y * BASE_RADIUS, z * BASE_RADIUS))
                norms.append((x, y, z))
                phases.append(np.random.rand() * 2 * math.pi)
                
                # More varied sensitivity based on position
                # Higher sensitivity at poles and equator
                lat_factor = abs(math.sin(theta * 2))  # Higher at equator and poles
                lon_factor = 1.0 + 0.3 * math.sin(phi * 4)  # Some longitudinal variation
                base_sens = 0.3 + 0.7 * np.random.rand()
                sens.append(base_sens * lat_factor * lon_factor)
                
                # Size variation based on sensitivity and position
                size_factor = 0.8 + 0.4 * np.random.rand()
                sizes.append(POINT_BASE_SIZE * size_factor)
                
        self.vertices = np.array(verts, dtype=np.float32)
        self.normals = np.array(norms, dtype=np.float32)
        self.phases = np.array(phases, dtype=np.float32)
        self.sensitivity = np.array(sens, dtype=np.float32)
        self.sizes = np.array(sizes, dtype=np.float32)
