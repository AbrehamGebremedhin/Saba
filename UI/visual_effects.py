"""
Advanced Visual Effects System for JARVIS-style Interface
Implements geometric patterns, wireframes, holographic effects, and dynamic data displays.
"""

import math
import time
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from OpenGL.GL import *
from OpenGL.GLU import *
from .color_scheme import color_scheme

class GeometricPatterns:
    """Generator for geometric patterns and wireframe overlays."""
    
    @staticmethod
    def draw_hexagonal_grid(center: Tuple[float, float, float], 
                           radius: float, 
                           layers: int = 3, 
                           alpha: float = 0.15):
        """Draw hexagonal grid pattern around a center point."""
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glLineWidth(0.8)
        
        color = color_scheme.get_color('accent', alpha * 0.3)
        glColor4f(*color)
        
        cx, cy, cz = center
        hex_radius = radius / (layers + 1)
        
        for layer in range(1, layers + 1):
            layer_radius = hex_radius * layer
            layer_alpha = alpha * (1.0 - layer * 0.2)
            
            color = color_scheme.get_color('accent', layer_alpha)
            glColor4f(*color)
            
            # Draw hexagon
            glBegin(GL_LINE_LOOP)
            for i in range(6):
                angle = i * math.pi / 3
                x = cx + layer_radius * math.cos(angle)
                z = cz + layer_radius * math.sin(angle)
                glVertex3f(x, cy, z)
            glEnd()
            
            # Draw connecting lines to center for inner layers
            if layer == 1:
                glBegin(GL_LINES)
                for i in range(6):
                    angle = i * math.pi / 3
                    x = cx + layer_radius * math.cos(angle)
                    z = cz + layer_radius * math.sin(angle)
                    glVertex3f(cx, cy, cz)
                    glVertex3f(x, cy, z)
                glEnd()
    
    @staticmethod
    def draw_triangular_pattern(center: Tuple[float, float, float], 
                               size: float, 
                               rotation: float = 0.0, 
                               alpha: float = 0.2):
        """Draw triangular geometric pattern."""
        glEnable(GL_BLEND)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glLineWidth(1.0)
        
        color = color_scheme.get_color('secondary', alpha)
        glColor4f(*color)
        
        cx, cy, cz = center
        
        glPushMatrix()
        glTranslatef(cx, cy, cz)
        glRotatef(rotation, 0, 1, 0)
        
        # Draw nested triangles
        for scale in [1.0, 0.6, 0.3]:
            s = size * scale
            triangle_alpha = alpha * scale
            
            color = color_scheme.get_color('secondary', triangle_alpha)
            glColor4f(*color)
            
            glBegin(GL_LINE_LOOP)
            for i in range(3):
                angle = i * 2 * math.pi / 3 + math.pi / 2
                x = s * math.cos(angle)
                z = s * math.sin(angle)
                glVertex3f(x, 0, z)
            glEnd()
        
        glPopMatrix()
    
    @staticmethod
    def draw_wireframe_sphere(center: Tuple[float, float, float], 
                             radius: float, 
                             segments: int = 16, 
                             alpha: float = 0.15):
        """Draw wireframe sphere overlay."""
        glEnable(GL_BLEND)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glLineWidth(0.6)
        
        cx, cy, cz = center
        
        glPushMatrix()
        glTranslatef(cx, cy, cz)
        
        # Latitude lines
        for i in range(segments // 4):
            lat_angle = math.pi * (i + 1) / (segments // 2)
            lat_radius = radius * math.sin(lat_angle)
            y_pos = radius * math.cos(lat_angle)
            
            fade = 1.0 - abs(i - segments // 8) / (segments // 8)
            color = color_scheme.get_color('primary', alpha * fade)
            glColor4f(*color)
            
            glBegin(GL_LINE_LOOP)
            for j in range(segments):
                angle = 2 * math.pi * j / segments
                x = lat_radius * math.cos(angle)
                z = lat_radius * math.sin(angle)
                glVertex3f(x, y_pos, z)
                glVertex3f(x, -y_pos, z)
            glEnd()
        
        # Longitude lines
        for i in range(segments // 2):
            lon_angle = 2 * math.pi * i / segments
            
            color = color_scheme.get_color('primary', alpha * 0.7)
            glColor4f(*color)
            
            glBegin(GL_LINE_STRIP)
            for j in range(segments + 1):
                lat_angle = math.pi * j / segments
                x = radius * math.sin(lat_angle) * math.cos(lon_angle)
                y = radius * math.cos(lat_angle)
                z = radius * math.sin(lat_angle) * math.sin(lon_angle)
                glVertex3f(x, y, z)
            glEnd()
        
        glPopMatrix()

class HolographicEffects:
    """Advanced holographic visual effects."""
    
    def __init__(self):
        self.scan_lines_enabled = True
        self.distortion_enabled = True
        self.glow_enabled = True
        
    def draw_scan_lines(self, width: int, height: int):
        """Draw CRT-style scan lines overlay."""
        if not self.scan_lines_enabled:
            return
            
        glDisable(GL_DEPTH_TEST)
        
        # Save matrices
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, width, 0, height, -1, 1)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        scan_params = color_scheme.apply_scan_lines(True)
        if scan_params['enabled']:
            spacing = scan_params['spacing']
            offset = scan_params['offset']
            color = scan_params['color']
            
            glColor4f(*color)
            glBegin(GL_LINES)
            
            y = offset % spacing
            while y < height:
                glVertex2f(0, y)
                glVertex2f(width, y)
                y += spacing
            
            glEnd()
        
        # Restore matrices
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        
        glEnable(GL_DEPTH_TEST)
    
    def draw_holographic_distortion(self, center: Tuple[float, float, float], 
                                   radius: float, 
                                   intensity: float = 1.0):
        """Draw holographic distortion effects around objects."""
        if not self.distortion_enabled:
            return
            
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)  # Additive blending for glow
        
        cx, cy, cz = center
        current_time = time.time()
        
        # Multiple distortion rings
        for i in range(3):
            ring_radius = radius * (1.3 + i * 0.4)
            ring_speed = 0.5 + i * 0.2
            ring_phase = current_time * ring_speed + i * 2.0
            
            # Fade based on distance from center
            fade = 1.0 / (1.0 + i * 0.5)
            alpha = 0.1 * intensity * fade
            
            color = color_scheme.get_dynamic_color('glow', intensity, ring_phase, alpha)
            glColor4f(*color)
            
            glPushMatrix()
            glTranslatef(cx, cy, cz)
            glRotatef(ring_phase * 20, 0, 1, 0)
            glRotatef(10 + i * 15, 1, 0, 1)
            
            # Draw distorted ring segments
            segments = 32
            segment_groups = 6
            segment_size = segments // segment_groups
            
            for group in range(segment_groups):
                # Skip some segments for broken/distorted look
                if (group + int(ring_phase)) % 3 == 0:
                    continue
                    
                glBegin(GL_LINE_STRIP)
                start_idx = group * segment_size
                for j in range(segment_size):
                    idx = start_idx + j
                    angle = 2 * math.pi * idx / segments
                    
                    # Add distortion
                    distortion = math.sin(angle * 4 + ring_phase) * 0.1
                    r = ring_radius * (1.0 + distortion)
                    
                    x = r * math.cos(angle)
                    z = r * math.sin(angle)
                    y = math.sin(angle * 3 + ring_phase) * 0.3
                    
                    glVertex3f(x, y, z)
                glEnd()
            
            glPopMatrix()
        
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_DEPTH_TEST)
    
    def draw_energy_pulse(self, center: Tuple[float, float, float], 
                         radius: float, 
                         pulse_phase: float = 0.0):
        """Draw energy pulse effect emanating from center."""
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        
        cx, cy, cz = center
        current_time = time.time() + pulse_phase
        
        # Multiple pulse waves
        for i in range(2):
            wave_time = current_time * (1.5 + i * 0.5)
            wave_radius = radius * (1.0 + (wave_time % 2.0))
            wave_alpha = max(0.0, 1.0 - (wave_time % 2.0)) * 0.2
            
            if wave_alpha > 0.01:
                color = color_scheme.get_dynamic_color('glow', 1.0, wave_time, wave_alpha)
                glColor4f(*color)
                
                glPushMatrix()
                glTranslatef(cx, cy, cz)
                
                glBegin(GL_LINE_LOOP)
                segments = 24
                for j in range(segments):
                    angle = 2 * math.pi * j / segments
                    x = wave_radius * math.cos(angle)
                    z = wave_radius * math.sin(angle)
                    glVertex3f(x, 0, z)
                glEnd()
                
                glPopMatrix()
        
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_DEPTH_TEST)

class DynamicDataDisplays:
    """Dynamic data visualization elements."""
    
    def __init__(self):
        self.build_in_speed = 2.0
        self.update_animation_speed = 1.5
        
    def draw_radial_graph(self, center: Tuple[float, float], 
                         radius: float, 
                         data: List[float], 
                         labels: Optional[List[str]] = None,
                         build_progress: float = 1.0):
        """Draw radial/polar graph with build-in animation."""
        if not data:
            return
            
        glDisable(GL_DEPTH_TEST)
        
        # Save matrices for 2D drawing
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        # Get viewport dimensions
        viewport = glGetIntegerv(GL_VIEWPORT)
        width, height = viewport[2], viewport[3]
        glOrtho(0, width, 0, height, -1, 1)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glEnable(GL_BLEND)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        
        cx, cy = center
        segments = len(data)
        max_value = max(data) if data else 1.0
        
        # Draw background circle
        color = color_scheme.get_color('secondary', 0.3)
        glColor4f(*color)
        glLineWidth(1.0)
        
        glBegin(GL_LINE_LOOP)
        for i in range(48):
            angle = 2 * math.pi * i / 48
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            glVertex2f(x, y)
        glEnd()
        
        # Draw radial grid lines
        grid_color = color_scheme.get_color('accent', 0.2)
        glColor4f(*grid_color)
        
        glBegin(GL_LINES)
        for i in range(segments):
            if i % (segments // 8) == 0:  # Only draw major grid lines
                angle = 2 * math.pi * i / segments - math.pi / 2
                x = cx + radius * math.cos(angle)
                y = cy + radius * math.sin(angle)
                glVertex2f(cx, cy)
                glVertex2f(x, y)
        glEnd()
        
        # Draw data bars with build-in animation
        bar_color = color_scheme.get_dynamic_color('primary', 1.0, 0.0, 0.8)
        glColor4f(*bar_color)
        glLineWidth(3.0)
        
        for i, value in enumerate(data):
            if build_progress * segments > i:
                angle = 2 * math.pi * i / segments - math.pi / 2
                bar_length = (value / max_value) * radius * 0.9
                
                # Build-in effect for current bar
                if i < build_progress * segments < i + 1:
                    bar_progress = (build_progress * segments) - i
                    bar_length *= bar_progress
                
                x1, y1 = cx, cy
                x2 = cx + bar_length * math.cos(angle)
                y2 = cy + bar_length * math.sin(angle)
                
                glBegin(GL_LINES)
                glVertex2f(x1, y1)
                glVertex2f(x2, y2)
                glEnd()
        
        # Restore matrices
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        
        glEnable(GL_DEPTH_TEST)
    
    def draw_floating_panel(self, position: Tuple[float, float, float], 
                           size: Tuple[float, float], 
                           rotation: Tuple[float, float, float] = (0, 0, 0),
                           alpha: float = 0.8):
        """Draw floating 3D panel with perspective and hover animation."""
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        px, py, pz = position
        width, height = size
        rx, ry, rz = rotation
        
        glPushMatrix()
        glTranslatef(px, py, pz)
        glRotatef(rx, 1, 0, 0)
        glRotatef(ry, 0, 1, 0)
        glRotatef(rz, 0, 0, 1)
        
        # Panel background with gradient effect
        glBegin(GL_QUADS)
        
        # Gradient from top to bottom
        top_color = color_scheme.get_color('background', alpha * 0.9)
        bottom_color = color_scheme.get_color('secondary', alpha * 0.3)
        
        # Top edge
        glColor4f(*top_color)
        glVertex3f(-width/2, height/2, 0)
        glVertex3f(width/2, height/2, 0)
        
        # Bottom edge
        glColor4f(*bottom_color)
        glVertex3f(width/2, -height/2, 0)
        glVertex3f(-width/2, -height/2, 0)
        
        glEnd()
        
        # Panel border
        border_color = color_scheme.get_color('accent', alpha * 0.6)
        glColor4f(*border_color)
        glLineWidth(1.5)
        
        glBegin(GL_LINE_LOOP)
        glVertex3f(-width/2, height/2, 0.01)
        glVertex3f(width/2, height/2, 0.01)
        glVertex3f(width/2, -height/2, 0.01)
        glVertex3f(-width/2, -height/2, 0.01)
        glEnd()
        
        glPopMatrix()

class ParticleTrails:
    """Enhanced particle trail effects with magnetic field simulation and varied types."""
    
    def __init__(self):
        self.max_particles = 200
        self.particles = []
        self.last_update = time.time()
    
    def add_spark_particle(self, position: Tuple[float, float, float], 
                          velocity: Tuple[float, float, float],
                          intensity: float = 1.0):
        """Add enhanced spark particles with different characteristics."""
        if len(self.particles) >= self.max_particles:
            self.particles.pop(0)  # Remove oldest particle
        
        import random
        
        # Create different particle types for variety
        particle_type = random.choice(['quick_flash', 'slow_fade', 'medium', 'trailing'])
        
        if particle_type == 'quick_flash':
            # Tiny, quick flashes - bright and fast
            particle = {
                'position': list(position),
                'velocity': [v * random.uniform(1.2, 2.0) for v in velocity],
                'life': random.uniform(0.3, 0.8),
                'max_life': 0.8,
                'size': random.uniform(1.0, 2.5),
                'color_base': [1.0, 0.95, 0.4],  # Bright white-gold
                'type': 'quick_flash',
                'magnetic_influence': 0.6,
                'birth_time': time.time(),
                'trail_length': 0
            }
        elif particle_type == 'slow_fade':
            # Larger, slower particles - warm and persistent
            particle = {
                'position': list(position),
                'velocity': [v * random.uniform(0.3, 0.7) for v in velocity],
                'life': random.uniform(2.0, 3.5),
                'max_life': 3.5,
                'size': random.uniform(2.5, 4.5),
                'color_base': [0.9, 0.7, 0.3],  # Warm gold
                'type': 'slow_fade',
                'magnetic_influence': 1.4,
                'birth_time': time.time(),
                'trail_length': 0
            }
        elif particle_type == 'trailing':
            # Particles that leave trails
            particle = {
                'position': list(position),
                'velocity': list(velocity),
                'life': random.uniform(1.5, 2.5),
                'max_life': 2.5,
                'size': random.uniform(1.8, 3.2),
                'color_base': [0.8, 0.6, 0.9],  # Slight purple tint
                'type': 'trailing',
                'magnetic_influence': 1.0,
                'birth_time': time.time(),
                'trail_positions': [list(position)],  # Store trail positions
                'trail_length': 8
            }
        else:
            # Medium particles (balanced)
            particle = {
                'position': list(position),
                'velocity': list(velocity),
                'life': random.uniform(1.0, 2.0),
                'max_life': 2.0,
                'size': random.uniform(2.0, 3.5),
                'color_base': [
                    random.uniform(0.7, 1.0),
                    random.uniform(0.6, 0.9),
                    random.uniform(0.2, 0.6)
                ],
                'type': 'medium',
                'magnetic_influence': 1.0,
                'birth_time': time.time(),
                'trail_length': 0
            }
        
        self.particles.append(particle)
    
    def add_particle(self, position: Tuple[float, float, float], 
                    velocity: Tuple[float, float, float],
                    life: float = 2.0,
                    size: float = 2.0):
        """Legacy method - redirect to enhanced spark particle system."""
        self.add_spark_particle(position, velocity, intensity=1.0)
    
    def update_particles(self):
        """Update particle positions with magnetic field simulation and curved paths."""
        current_time = time.time()
        dt = current_time - self.last_update
        self.last_update = current_time
        
        # Update existing particles
        alive_particles = []
        for particle in self.particles:
            particle['life'] -= dt
            if particle['life'] > 0:
                # Store old position for trailing particles
                if particle['type'] == 'trailing':
                    particle['trail_positions'].append(list(particle['position']))
                    if len(particle['trail_positions']) > particle['trail_length']:
                        particle['trail_positions'].pop(0)
                
                # Update position
                for i in range(3):
                    particle['position'][i] += particle['velocity'][i] * dt
                
                # Magnetic field simulation - creates curved paths
                magnetic_strength = particle['magnetic_influence']
                sphere_attraction = 0.3 * magnetic_strength
                
                # Calculate distance from center for magnetic field effect
                distance = math.sqrt(sum(p**2 for p in particle['position']))
                if distance > 0:
                    # Radial force (toward center)
                    radial_force = sphere_attraction / (1.0 + distance * 0.5)
                    for i in range(3):
                        particle['velocity'][i] -= particle['position'][i] * radial_force * dt
                    
                    # Tangential force (creates curved motion)
                    tangential_strength = 0.8 * magnetic_strength
                    if particle['type'] == 'quick_flash':
                        tangential_strength *= 1.5  # More erratic for quick flashes
                    
                    # Cross product for tangential force (simulates magnetic field)
                    tangential = [
                        particle['position'][1] * tangential_strength * dt,
                        -particle['position'][0] * tangential_strength * dt,
                        particle['position'][2] * tangential_strength * 0.3 * dt
                    ]
                    
                    for i in range(3):
                        particle['velocity'][i] += tangential[i]
                
                # Type-specific behaviors
                if particle['type'] == 'quick_flash':
                    # Add some random jitter for erratic movement
                    import random
                    jitter = 0.02
                    for i in range(3):
                        particle['velocity'][i] += random.uniform(-jitter, jitter)
                elif particle['type'] == 'slow_fade':
                    # Slower, more graceful movement
                    drag = 0.98
                    for i in range(3):
                        particle['velocity'][i] *= drag
                
                # General air resistance
                drag = 0.96 if particle['type'] != 'slow_fade' else 0.98
                for i in range(3):
                    particle['velocity'][i] *= drag
                
                alive_particles.append(particle)
        
        self.particles = alive_particles
    
    def draw_particles(self):
        """Draw all active particles with enhanced visuals and trails."""
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)  # Additive blending for glow
        glEnable(GL_POINT_SMOOTH)
        
        for particle in self.particles:
            life_ratio = particle['life'] / particle['max_life']
            
            # Type-specific alpha calculations
            if particle['type'] == 'quick_flash':
                # Sharp peak then fast fade
                alpha = min(1.0, life_ratio * 2.0) * 0.9
                if life_ratio < 0.3:
                    alpha *= (life_ratio / 0.3)
            elif particle['type'] == 'slow_fade':
                # Gentle, sustained glow
                alpha = life_ratio * 0.7
            else:
                # Standard fade
                alpha = life_ratio * 0.8
            
            if alpha > 0.01:
                # Calculate size based on particle type and life
                if particle['type'] == 'quick_flash':
                    size = particle['size'] * (0.8 + 0.4 * math.sin(life_ratio * math.pi))
                elif particle['type'] == 'slow_fade':
                    size = particle['size'] * (0.6 + 0.4 * life_ratio)
                else:
                    size = particle['size'] * (0.5 + 0.5 * life_ratio)
                
                # Color calculation with dynamic effects
                base_color = particle['color_base']
                age = time.time() - particle['birth_time']
                
                # Add some color variation based on age and type
                color = []
                for i, base in enumerate(base_color):
                    if particle['type'] == 'quick_flash':
                        # Bright, flickering
                        flicker = 1.0 + 0.2 * math.sin(age * 20)
                        color.append(min(1.0, base * flicker))
                    elif particle['type'] == 'slow_fade':
                        # Warm, stable
                        warmth = 1.0 + 0.1 * math.sin(age * 2)
                        color.append(base * warmth)
                    else:
                        # Standard with slight shimmer
                        shimmer = 1.0 + 0.05 * math.sin(age * 8)
                        color.append(base * shimmer)
                
                color.append(alpha)  # Add alpha
                glColor4f(*color)
                
                # Draw trailing particles
                if particle['type'] == 'trailing' and 'trail_positions' in particle:
                    glLineWidth(2.0)
                    glBegin(GL_LINE_STRIP)
                    for j, trail_pos in enumerate(particle['trail_positions']):
                        trail_alpha = alpha * (j / len(particle['trail_positions'])) * 0.5
                        trail_color = color[:3] + [trail_alpha]
                        glColor4f(*trail_color)
                        glVertex3f(*trail_pos)
                    glEnd()
                
                # Draw main particle
                glPointSize(size)
                glBegin(GL_POINTS)
                glVertex3f(*particle['position'])
                glEnd()
        
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_DEPTH_TEST)

# Global instances
geometric_patterns = GeometricPatterns()
holographic_effects = HolographicEffects()
data_displays = DynamicDataDisplays()
particle_system = ParticleTrails()
