import math
import numpy as np

LAT_STEPS = 72
LON_STEPS = 144
BASE_RADIUS = 3.0
POINT_BASE_SIZE = 3.0

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
                sens.append(np.random.rand())
                sizes.append(POINT_BASE_SIZE * (0.9 + np.random.rand() * 1.2))
        self.vertices = np.array(verts, dtype=np.float32)
        self.normals = np.array(norms, dtype=np.float32)
        self.phases = np.array(phases, dtype=np.float32)
        self.sensitivity = np.array(sens, dtype=np.float32)
        self.sizes = np.array(sizes, dtype=np.float32)
