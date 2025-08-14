
import time
import math
import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *

from .models import SphereModel, LAT_STEPS, LON_STEPS, BASE_RADIUS
from .audio_analyzer import AudioAnalyzer
from .color_scheme import color_scheme
from .visual_effects import geometric_patterns, holographic_effects, data_displays, particle_system
from .typography import typography
from config.logger import get_logger

logger = get_logger(__name__)

FPS_TARGET = 60

class SabaGL(QOpenGLWidget):
    audio_finished = pyqtSignal()
    status_update = pyqtSignal(str, bool)  # status, show_progress

    def __init__(self, wav_path):
        super().__init__()
        self.setMinimumSize(900, 700)
        self.model = SphereModel()
        self.audio = AudioAnalyzer(wav_path)
        self.rotation = 0.0
        
        # FPS tracking
        self._frame_counter = 0
        self._fps = 0.0
        self._last_fps_ts = time.time()
        
        # Timer for scene updates
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_scene)
        self.timer.start(int(1000 / FPS_TARGET))
        
        # Initialize color scheme to standby mode
        color_scheme.set_mode("standby", 0.5)
        
        # Enhanced holographic effect parameters
        self.effects_params = color_scheme.get_holographic_effects()
        
        # Point density controls for cleaner sampling
        self.stride_lat_core = 2
        self.stride_lon_core = 2
        self.stride_lat_glow = 1
        self.stride_lon_glow = 2
        self.sample_indices_core = self._build_strided_indices(self.stride_lat_core, self.stride_lon_core)
        self.sample_indices_glow = self._build_strided_indices(self.stride_lat_glow, self.stride_lon_glow)
        
        # Track audio and status
        self._audio_playing = False
        self._current_status = "Standby"
        
        # Enhanced sphere effects
        self.sphere_breathing = True
        self.energy_pulses = True
        
        # Emit initial status
        self.status_update.emit("Interface Initialized", False)

    def initializeGL(self):
        # Near-black background for cinematic JARVIS look
        glClearColor(0.02, 0.02, 0.05, 1.0)  # Very dark with subtle blue hint
        
        # Enhanced point rendering with superior anti-aliasing
        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_PROGRAM_POINT_SIZE)
        glEnable(GL_DEPTH_TEST)
        glHint(GL_POINT_SMOOTH_HINT, GL_NICEST)
        
        # Superior line rendering with anti-aliasing
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        
        # Multi-sampling anti-aliasing for crystal clear rendering
        glEnable(GL_MULTISAMPLE)
        
        # Enhanced depth testing with improved precision
        glDepthFunc(GL_LEQUAL)
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
        
        # Additional refinements for crystal clear visuals
        glHint(GL_POLYGON_SMOOTH_HINT, GL_NICEST)
        glEnable(GL_POLYGON_SMOOTH)
        
        # Improved color precision
        glShadeModel(GL_SMOOTH)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, w / max(1.0, h), 0.1, 50.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Enhanced background with dynamic gradient
        self._draw_background_gradient()
        
        # Draw holographic scan lines overlay
        holographic_effects.draw_scan_lines(self.width(), self.height())

        # 3D camera setup
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -10.0)
        glRotatef(20, 1, 0, 0)
        glRotatef(self.rotation, 0, 1, 0)

        rms, spec = self.audio.analyze()
        global_intensity = min(1.0, 0.6 + rms * 5.0)
        
        # Update color scheme based on current status
        if self._current_status == "Processing":
            color_scheme.set_mode("processing", 0.5)
            global_intensity = max(global_intensity, 0.8 + math.sin(time.time() * 4.0) * 0.2)
        elif self._current_status == "Listening":
            color_scheme.set_mode("listening", 0.5)
        elif self._current_status == "Playing Audio":
            color_scheme.set_mode("active", 0.5)
        else:
            color_scheme.set_mode("standby", 0.5)
        
        # Get current effect parameters
        effects = color_scheme.get_holographic_effects()

        # Enhanced sphere movement and breathing
        if rms > 0.02 or self._current_status == "Processing":
            sway_x = math.sin(time.time() * 0.8) * rms * 0.15
            sway_y = math.cos(time.time() * 0.6) * rms * 0.1
            glTranslatef(sway_x, sway_y, 0.0)
            
            # Enhanced breathing effect
            breath_scale = 1.0 + rms * 0.05
            if self._current_status == "Processing":
                breath_scale += math.sin(time.time() * 3.0) * 0.02
            glScalef(breath_scale, breath_scale, breath_scale)

        # Enhanced multi-pass rendering for JARVIS-style sphere
        
        # Pass 1: Strong outer glow
        self._draw_sphere_points(
            global_intensity,
            spec,
            alpha=effects['glow_alpha'],
            size_multiplier=effects['glow_intensity'],
            depth_test=False,
            with_fresnel=False,
            with_scan=False,
            indices=self.sample_indices_glow,
        )

        # Pass 2: Main sphere core
        self._draw_sphere_points(
            global_intensity,
            spec,
            alpha=effects['core_alpha'],
            size_multiplier=1.2,
            depth_test=True,
            with_fresnel=True,
            with_scan=True,
            with_backface_fade=True,
            indices=self.sample_indices_core,
        )
        
        # Pass 3: Bright inner core
        self._draw_sphere_points(
            global_intensity,
            spec,
            alpha=min(1.0, effects['core_alpha'] * 1.1),
            size_multiplier=0.6,
            depth_test=True,
            with_fresnel=False,
            with_scan=True,
            indices=self.sample_indices_core,
        )
        
        # Central glowing power core
        self._draw_central_core(global_intensity, effects)

        # Enhanced orbiting rings
        self._draw_orbit_rings(global_intensity, effects)
        
        # Draw advanced geometric patterns
        geometric_patterns.draw_wireframe_sphere(
            (0, 0, 0), 
            BASE_RADIUS * 1.8, 
            segments=24, 
            alpha=0.1
        )
        
        # Draw holographic distortion effects
        holographic_effects.draw_holographic_distortion(
            (0, 0, 0), 
            BASE_RADIUS, 
            global_intensity
        )
        
        # Update and draw enhanced particle trails
        particle_system.update_particles()
        if rms > 0.05:  # Add varied particles during high activity
            import random
            for _ in range(int(rms * 8)):  # More particles for better effect
                # Generate particles from sphere surface with magnetic field influence
                angle1 = random.uniform(0, 2 * math.pi)
                angle2 = random.uniform(0, math.pi)
                
                # Position on sphere surface
                sphere_radius = BASE_RADIUS * random.uniform(0.8, 1.1)
                pos = (
                    sphere_radius * math.sin(angle2) * math.cos(angle1),
                    sphere_radius * math.cos(angle2),
                    sphere_radius * math.sin(angle2) * math.sin(angle1)
                )
                
                # Velocity with outward bias and some tangential component
                vel_magnitude = random.uniform(0.3, 1.2) * rms
                vel = (
                    pos[0] * vel_magnitude * 0.5 + random.uniform(-0.3, 0.3),
                    pos[1] * vel_magnitude * 0.3 + random.uniform(-0.2, 0.4),
                    pos[2] * vel_magnitude * 0.5 + random.uniform(-0.3, 0.3)
                )
                
                particle_system.add_spark_particle(pos, vel, intensity=rms)
        
        particle_system.draw_particles()

        # Draw subtle background grid for depth
        self._draw_background_grid(effects)

        # Minimal HUD elements
        self._draw_hud_overlay(effects)

        # Subtle vignette for cinematic effect
        self._draw_vignette_overlay(effects)
        
        # Screen-wide scan line overlay for holographic feel
        self._draw_scanline_overlay(effects)

    def load_audio(self, wav_path):
        """Load a new audio file and restart audio analysis."""
        try:
            self.audio = AudioAnalyzer(wav_path)
            self.status_update.emit("Audio Loaded", False)
            logger.info(f"Loaded new audio file: {wav_path}")
        except Exception as e:
            self.status_update.emit("Audio Load Failed", False)
            logger.error(f"Error loading audio file {wav_path}: {e}")

    def play_audio(self):
        """Manually trigger audio playback and emit audio_finished when done."""
        try:
            if self.audio:
                self._audio_playing = True
                self.status_update.emit("Playing Audio", False)
                def on_audio_done():
                    self._audio_playing = False
                    self.status_update.emit("Standby", False)
                    self.audio_finished.emit()
                QtCore.QTimer.singleShot(300, lambda: self._play_and_emit(on_audio_done))
                logger.info("Audio playback triggered")
        except Exception as e:
            self.status_update.emit("Playback Error", False)
            logger.error(f"Error triggering audio playback: {e}")

    def _play_and_emit(self, on_done):
        """Play audio and call on_done when finished."""
        try:
            if self.audio:
                self.audio.play(callback=on_done)
            else:
                on_done()
        except Exception as e:
            logger.error(f"Error in _play_and_emit: {e}")
            on_done()

    def is_audio_playing(self):
        """Return True if audio is currently playing."""
        return self._audio_playing
        
    def set_thinking_mode(self, thinking=True):
        """Set visual indicators for when Saba is thinking/processing"""
        if thinking:
            self._current_status = "Processing"
            color_scheme.set_mode("processing", 1.0)
            self.status_update.emit("Processing Input", True)
        else:
            self._current_status = "Standby"
            color_scheme.set_mode("standby", 1.0)
            self.status_update.emit("Standby", False)

    def update_scene(self):
        rms, spec = self.audio.analyze()
        
        # Very slow base rotation speed
        base_speed = 0.02  # Much slower base rotation
        
        # Very gentle audio-responsive rotation speed
        if rms > 0.02:  # Higher threshold
            # Very small increase in rotation speed based on audio intensity
            audio_speed = rms * 0.08  # Much smaller audio influence
            self.rotation += base_speed + audio_speed
        else:
            # Very slow rotation when no audio
            self.rotation += base_speed * 0.3  # Even slower when quiet
            
        # Update FPS counter
        now = time.time()
        self._frame_counter += 1
        elapsed = now - self._last_fps_ts
        if elapsed >= 0.5:
            self._fps = self._frame_counter / max(1e-6, elapsed)
            self._frame_counter = 0
            self._last_fps_ts = now

        self.update()

    # ---------- Saba-style UI helpers ----------

    def _draw_background_gradient(self):
        """Enhanced holographic background with subtle grid pattern."""
        glDisable(GL_DEPTH_TEST)

        # Save matrices
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(-1, 1, -1, 1, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        current_time = time.time()
        
        # Base background gradient (near-black with subtle variations)
        glBegin(GL_QUADS)
        # Bottom - very dark with subtle red tint
        glColor4f(0.02, 0.01, 0.03, 1.0)
        glVertex2f(-1.0, -1.0)
        glVertex2f(1.0, -1.0)
        # Top - dark with subtle blue tint
        glColor4f(0.01, 0.02, 0.05, 1.0)
        glVertex2f(1.0, 1.0)
        glVertex2f(-1.0, 1.0)
        glEnd()
        
        # Holographic grid pattern overlay
        grid_alpha = 0.04 + 0.02 * math.sin(current_time * 0.6)
        grid_color = (0.0, 0.2, 0.4, grid_alpha)  # Subtle cyan grid
        
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glLineWidth(0.3)
        glColor4f(*grid_color)
        
        # Vertical grid lines with subtle animation
        for x in [-0.8, -0.4, 0.0, 0.4, 0.8]:
            x_offset = x + 0.005 * math.sin(current_time * 0.3 + x * 3.0)
            glBegin(GL_LINES)
            glVertex2f(x_offset, -1.0)
            glVertex2f(x_offset, 1.0)
            glEnd()
        
        # Horizontal grid lines with subtle animation
        for y in [-0.6, -0.2, 0.2, 0.6]:
            y_offset = y + 0.004 * math.cos(current_time * 0.4 + y * 3.5)
            glBegin(GL_LINES)
            glVertex2f(-1.0, y_offset)
            glVertex2f(1.0, y_offset)
            glEnd()
        
        # Floating particles for depth
        glPointSize(1.2)
        particle_color = (0.05, 0.3, 0.6, 0.15)
        
        glBegin(GL_POINTS)
        # Background particles with subtle movement
        for i in range(12):
            # Pseudo-random positions
            base_x = math.sin(i * 2.1) * 0.9
            base_y = math.cos(i * 1.8) * 0.8
            
            # Slow drift animation
            drift_x = base_x + 0.02 * math.sin(current_time * 0.2 + i)
            drift_y = base_y + 0.015 * math.cos(current_time * 0.15 + i * 1.3)
            
            # Subtle twinkle
            twinkle = 1.0 + 0.4 * math.sin(current_time * 1.5 + i * 0.7)
            particle_alpha = particle_color[3] * twinkle
            
            if particle_alpha > 0.05:
                glColor4f(particle_color[0], particle_color[1], particle_color[2], particle_alpha)
                glVertex2f(drift_x, drift_y)
        glEnd()
        
        # Restore matrices
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

        glEnable(GL_DEPTH_TEST)
        
    def _draw_holographic_distortion(self, global_intensity):
        """Add subtle holographic distortion effects around the sphere"""
        if not self.holographic_distortion:
            return
            
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glLineWidth(1.0)
        
        # Distortion rings at various distances
        time_s = time.time()
        distortion_rings = [BASE_RADIUS * r for r in (1.5, 2.1, 2.8)]
        
        for i, radius in enumerate(distortion_rings):
            glPushMatrix()
            # Different rotation speeds for each ring
            glRotatef((time_s * (8.0 + i * 3.0)) % 360.0, 0, 1, 0)
            glRotatef(5.0 + i * 8.0, 1, 0, 1)
            
            # Flickering intensity
            flicker = 0.3 + 0.7 * (0.5 + 0.5 * math.sin(time_s * (15.0 + i * 5.0)))
            alpha = self.ring_alpha * 0.4 * flicker * global_intensity
            glColor4f(0.1, 0.4, 0.8, alpha)
            
            # Draw distorted circle segments
            segments = 80
            segment_len = 8
            gap_len = 4
            step = 2.0 * math.pi / float(segments)
            
            s = 0
            while s < segments:
                glBegin(GL_LINE_STRIP)
                for k in range(segment_len):
                    idx = s + k
                    if idx >= segments:
                        break
                    angle = step * idx
                    # Add distortion
                    distort = math.sin(angle * 3.0 + time_s * 2.0) * 0.1
                    r = radius + distort
                    x = math.cos(angle) * r
                    z = math.sin(angle) * r
                    y = math.sin(angle * 2.0 + time_s) * 0.2
                    glVertex3f(x, y, z)
                glEnd()
                s += segment_len + gap_len
                
            glPopMatrix()
            
        glEnable(GL_DEPTH_TEST)
        
    def _draw_data_streams(self, global_intensity):
        """Draw data stream effects around the visualization"""
        glDisable(GL_DEPTH_TEST)
        
        # Project to screen-space
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(-1, 1, -1, 1, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glLineWidth(1.0)
        
        time_s = time.time()
        
        # Vertical data streams on the sides
        stream_positions = [-0.9, -0.7, 0.7, 0.9]
        for x_pos in stream_positions:
            # Multiple streams at different speeds
            for stream_id in range(3):
                offset = (time_s * (0.5 + stream_id * 0.2)) % 3.0 - 1.5
                alpha = max(0.0, 1.0 - abs(offset) / 1.5) * 0.3 * global_intensity
                
                glColor4f(0.2, 0.6, 1.0, alpha)
                glBegin(GL_LINE_STRIP)
                
                # Draw stream segment
                segment_length = 0.4
                steps = 20
                for i in range(steps):
                    y = offset + (i / float(steps - 1)) * segment_length
                    if -1.0 <= y <= 1.0:
                        # Add slight horizontal variation
                        x_var = math.sin(y * 10.0 + time_s * 3.0) * 0.02
                        glVertex2f(x_pos + x_var, y)
                        
                glEnd()
        
        # Restore matrices
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        
        glEnable(GL_DEPTH_TEST)

    def _build_strided_indices(self, stride_lat: int, stride_lon: int):
        """Create evenly distributed indices across latitude/longitude for a tidy grid sampling."""
        indices = []
        # SphereModel is built row-major: for each lat (i) we add all lon (j)
        for i in range(0, LAT_STEPS + 1, max(1, stride_lat)):
            base = i * LON_STEPS
            for j in range(0, LON_STEPS, max(1, stride_lon)):
                idx = base + j
                if idx < len(self.model.vertices):
                    indices.append(idx)
        return np.array(indices, dtype=np.int32)

    def _draw_sphere_points(self, global_intensity, spec, alpha=0.9, size_multiplier=1.0, 
                           depth_test=True, with_fresnel=False, with_scan=False, 
                           with_backface_fade=False, indices=None):
        """Draw sphere points with crystal clear, refined JARVIS-style rendering."""
        if depth_test:
            glEnable(GL_DEPTH_TEST)
        else:
            glDisable(GL_DEPTH_TEST)

        # Get current effect parameters
        effects = color_scheme.get_holographic_effects()

        # Refined point sizing for crystal clarity
        if hasattr(self.model.sizes, '__len__') and len(self.model.sizes) > 0:
            avg_size = float(np.sum(self.model.sizes)) / float(len(self.model.sizes))
        else:
            avg_size = 3.5  # Slightly smaller for better definition
        
        # Crystal clear point sizing
        base_size = max(2.5, avg_size * size_multiplier * 1.0)  # Reduced multiplier for clarity
        glPointSize(base_size)
        
        # Enhanced blending for crystal clear edges
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glBegin(GL_POINTS)
        current_time = time.time()
        
        # Refined organic time flows with smoother animation
        flow_time = current_time * effects['scan_speed'] * 1.5
        energy_time = current_time * effects['pulse_speed'] * 0.8
        
        # Smoother wave patterns for refined look
        wave_phase1 = math.sin(energy_time * 0.6) * 1.8
        wave_phase2 = math.cos(energy_time * 0.4) * 1.5
        wave_phase3 = math.sin(energy_time * 1.0) * 1.2
        
        # Model rotations for fresnel/backface calculations
        rot_y = math.radians(self.rotation)
        cy, sy = math.cos(rot_y), math.sin(rot_y)
        rot_x = math.radians(20.0)
        cx, sx = math.cos(rot_x), math.sin(rot_x)

        # More stable energy flow centers
        flow_center_x = math.sin(energy_time * 0.25) * 0.6
        flow_center_y = math.cos(energy_time * 0.3) * 0.5
        flow_center_z = math.sin(energy_time * 0.28) * 0.55

        if indices is None:
            indices_iter = range(len(self.model.vertices))
        else:
            indices_iter = indices

        for idx in indices_iter:
            vx, vy, vz = self.model.vertices[idx]
            nx, ny, nz = self.model.normals[idx]
            phase = self.model.phases[idx]
            sensitivity = self.model.sensitivity[idx]

            # Refined energy flow calculation
            dist_to_flow = math.sqrt(
                (vx - flow_center_x)**2 + 
                (vy - flow_center_y)**2 + 
                (vz - flow_center_z)**2
            ) / BASE_RADIUS
            
            # Smoother wave patterns for cleaner look
            wave1 = math.sin(phase + flow_time * 2.5 + wave_phase1)
            wave2 = math.cos(phase * 1.5 + flow_time * 2.0 + wave_phase2)
            wave3 = math.sin(phase * 0.7 + flow_time * 1.5 + wave_phase3)
            
            # More subtle organic pattern for refined appearance
            organic_pattern = (wave1 + wave2 * 0.6 + wave3 * 0.4) / 3.2
            
            # Enhanced but more subtle energy flow effect
            flow_intensity = max(0.3, 1.0 - dist_to_flow * 0.7)
            flow_displacement = organic_pattern * 0.06 * flow_intensity  # Reduced for clarity
            
            # Audio response with better control
            band_value = 0.0
            if spec is not None:
                latitude_band = int(((ny + 1.0) * 0.5) * len(spec))
                band_value = spec[min(len(spec) - 1, latitude_band)] if latitude_band < len(spec) else 0.0

            # More controlled displacement
            audio_displacement = sensitivity * band_value * 0.12  # Reduced for cleaner look
            total_displacement = flow_displacement + audio_displacement
            
            # Apply displacement
            px = vx + nx * total_displacement
            py = vy + ny * total_displacement
            pz = vz + nz * total_displacement

            # Enhanced energy intensity with better range control
            base_intensity = global_intensity * (0.5 + 0.5 * sensitivity)  # Better base range
            flow_boost = flow_intensity * 0.4  # Reduced for subtlety
            audio_boost = audio_displacement * 2.5
            
            intensity = min(1.0, base_intensity + flow_boost + audio_boost)

            # Refined fresnel rim lighting
            view_nz = 0.0
            if with_fresnel or with_backface_fade:
                # Transform normal to view space
                nxp = nx * cy + nz * -sy
                nzp = nx * sy + nz * cy
                nyp = ny
                nxx = nxp
                nyy = nyp * cx - nzp * sx
                nzz = nyp * sx + nzp * cx
                view_nz = nzz
                
                if with_fresnel:
                    fresnel = max(0.0, 1.0 - abs(view_nz))
                    intensity += effects['fresnel_strength'] * 0.8 * (fresnel ** 2.0) * flow_intensity

            # Enhanced energy band scanning with cleaner edges
            if with_scan:
                scan_center_y = math.sin(current_time * effects['scan_speed'] * 0.8) * (BASE_RADIUS * 0.7)
                scan_thickness = effects['scan_width'] * BASE_RADIUS * 0.5
                dy = abs(vy - scan_center_y)
                if dy < scan_thickness:
                    scan_factor = 1.0 - (dy / scan_thickness)
                    # Smoother scan band edges
                    scan_intensity = 0.3 * (scan_factor ** 2.0) * flow_intensity
                    intensity += scan_intensity

            # JARVIS-style warm gold color with dynamic ripple effects
            energy_mix = intensity * flow_intensity
            
            # Add holographic ripple waves across the surface
            surface_ripple = math.sin(vx * 8.0 + current_time * 3.5) * math.cos(vy * 6.0 + current_time * 2.8)
            surface_ripple += math.sin(vz * 7.0 + current_time * 4.2) * 0.5
            ripple_intensity = energy_mix * (1.0 + surface_ripple * 0.2)
            
            # Low-frequency pulse across the entire sphere
            global_pulse = 1.0 + 0.15 * math.sin(current_time * 1.2)
            pulse_intensity = ripple_intensity * global_pulse
            
            # Warm gold color palette for JARVIS aesthetic with dynamic variations
            if pulse_intensity > 0.8:
                # Bright gold for high energy with ripple enhancement
                base_color = (1.0, 0.9, 0.35, alpha * 0.95)
                color = (
                    base_color[0] * pulse_intensity * 1.1,
                    base_color[1] * pulse_intensity * 1.0,
                    base_color[2] * pulse_intensity * 0.85,
                    base_color[3]
                )
            elif pulse_intensity > 0.5:
                # Medium warm gold with shimmer
                base_color = (0.95, 0.75, 0.3, alpha * 0.9)
                shimmer = 1.0 + 0.1 * math.sin(phase + current_time * 5.0)
                color = (
                    base_color[0] * pulse_intensity * shimmer,
                    base_color[1] * pulse_intensity * shimmer * 0.95,
                    base_color[2] * pulse_intensity * shimmer * 0.8,
                    base_color[3]
                )
            else:
                # Deep amber for low energy areas with subtle glow
                base_color = (0.85, 0.6, 0.25, alpha * 0.8)
                color = (
                    base_color[0] * pulse_intensity * 0.9,
                    base_color[1] * pulse_intensity * 0.9,
                    base_color[2] * pulse_intensity * 0.75,
                    base_color[3]
                )
            
            # Holographic field effect - makes wireframe appear as energy field
            holographic_boost = 0.2 * math.sin(current_time * 4.0 + phase) * flow_intensity
            color = (
                min(1.0, color[0] + holographic_boost),
                min(1.0, color[1] + holographic_boost * 0.8),
                min(1.0, color[2] + holographic_boost * 0.5),
                color[3]
            )
            
            # Refined backface fading for crystal clear depth
            if with_backface_fade and view_nz != 0.0:
                facing = max(0.0, 0.4 + 0.6 * (-view_nz))  # Better depth perception
                final_alpha = color[3] * (0.5 + 0.5 * facing)
                color = (color[0], color[1], color[2], final_alpha)

            glColor4f(*color)
            glVertex3f(px, py, pz)
            
        glEnd()
        
        # Reset blending to standard
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
    def _draw_central_core(self, global_intensity, effects):
        """Draw the central shimmering power core with holographic ripples."""
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)  # Additive blending for glow
        
        current_time = time.time()
        
        # Advanced pulsing with multiple harmonics for organic feel
        pulse1 = 1.0 + 0.3 * math.sin(current_time * 2.2)
        pulse2 = 1.0 + 0.2 * math.sin(current_time * 3.7)
        pulse3 = 1.0 + 0.15 * math.sin(current_time * 1.8)
        core_intensity = global_intensity * (pulse1 * pulse2 * pulse3) * 0.4
        
        # Shimmering effect with ripple waves
        shimmer = 1.0 + 0.4 * math.sin(current_time * 6.5) * math.cos(current_time * 4.2)
        
        # Multi-layer core for depth and complexity
        core_layers = [
            {'size': 15.0, 'color': (1.0, 1.0, 0.95, 0.6), 'intensity': 1.4, 'shimmer': True},  # Outer shimmer
            {'size': 10.0, 'color': (1.0, 0.95, 0.8, 0.8), 'intensity': 1.2, 'shimmer': True},  # Bright white core
            {'size': 7.0, 'color': (1.0, 0.85, 0.3, 0.95), 'intensity': 1.0, 'shimmer': False}, # Warm yellow
            {'size': 4.0, 'color': (1.0, 0.7, 0.1, 1.0), 'intensity': 0.8, 'shimmer': False},   # Golden center
            {'size': 2.0, 'color': (0.9, 0.6, 0.05, 1.0), 'intensity': 0.6, 'shimmer': False}, # Deep core
        ]
        
        for layer in core_layers:
            size = layer['size']
            color = layer['color']
            intensity = layer['intensity'] * core_intensity
            
            # Apply shimmer effect to outer layers
            if layer['shimmer']:
                intensity *= (1.0 + shimmer * 0.3)
            
            # Apply intensity to color with subtle variations
            final_color = (
                min(1.0, color[0] * intensity),
                min(1.0, color[1] * intensity),
                min(1.0, color[2] * intensity),
                color[3] * global_intensity * 0.9
            )
            
            glPointSize(size)
            glColor4f(*final_color)
            
            glBegin(GL_POINTS)
            # Add subtle position variation for shimmer
            if layer['shimmer']:
                shimmer_x = math.sin(current_time * 8.3) * 0.01
                shimmer_y = math.cos(current_time * 7.1) * 0.01
                glVertex3f(shimmer_x, shimmer_y, 0.0)
            else:
                glVertex3f(0.0, 0.0, 0.0)
            glEnd()
        
        # Add reflective highlight - moving point of light on sphere surface
        self._draw_sphere_highlight(core_intensity, global_intensity, current_time)
        
        # Holographic ripple rings around core
        glLineWidth(1.0)
        ripple_time = current_time * 2.5
        
        for ripple_idx in range(5):
            # Ripple expands outward from center
            base_radius = 0.05 + ripple_idx * 0.04
            ripple_phase = ripple_time - ripple_idx * 0.8
            ripple_radius = base_radius + 0.02 * math.sin(ripple_phase)
            
            # Fading ripples
            ripple_alpha = max(0.0, 0.4 * math.cos(ripple_phase * 0.5))
            
            if ripple_alpha > 0.05:  # Only draw visible ripples
                ripple_color = (
                    0.8 * core_intensity,
                    0.6 * core_intensity,
                    0.2 * core_intensity,
                    ripple_alpha * global_intensity
                )
                glColor4f(*ripple_color)
                
                glBegin(GL_LINE_LOOP)
                segments = 20
                for i in range(segments):
                    angle = 2.0 * math.pi * i / segments
                    x = math.cos(angle) * ripple_radius
                    y = math.sin(angle) * ripple_radius
                    # Add subtle 3D ripple effect
                    z = math.sin(angle * 3.0 + ripple_phase) * 0.005
                    glVertex3f(x, y, z)
                glEnd()
        
        # Energy field patterns rotating around core
        glLineWidth(1.2)
        field_rotation = current_time * 1.2
        
        for field_idx in range(4):
            field_radius = 0.18 + field_idx * 0.03
            rotation_offset = field_idx * (math.pi / 2)
            field_phase = field_rotation + rotation_offset
            
            # Energy field color with variation
            field_intensity = 0.8 + 0.3 * math.sin(current_time * 3.0 + field_idx)
            field_color = (
                0.9 * core_intensity * field_intensity,
                0.5 * core_intensity * field_intensity,
                0.1 * core_intensity * field_intensity,
                0.3 * global_intensity
            )
            glColor4f(*field_color)
            
            # Draw energy field segments (not complete circles)
            segments_per_ring = 12
            segment_gap = 2  # Gap between segments
            
            for seg in range(0, segments_per_ring, segment_gap):
                glBegin(GL_LINE_STRIP)
                for i in range(segment_gap):
                    if seg + i < segments_per_ring:
                        angle = (2.0 * math.pi * (seg + i) / segments_per_ring) + field_phase
                        x = math.cos(angle) * field_radius
                        y = math.sin(angle) * field_radius
                        # Dynamic Z variation for 3D field effect
                        z = math.sin(angle * 2.0 + current_time * 1.5) * 0.015
                        glVertex3f(x, y, z)
                glEnd()
        
        # Reset blending and depth test
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_DEPTH_TEST)

    def _draw_sphere_highlight(self, core_intensity, global_intensity, current_time):
        """Draw reflective highlight that moves across the sphere surface."""
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        
        # Moving light source simulation
        light_angle = current_time * 0.8  # Slow rotation
        light_height = 0.6 + 0.3 * math.sin(current_time * 0.3)  # Subtle vertical movement
        
        # Calculate highlight position on sphere surface
        highlight_x = BASE_RADIUS * 0.3 * math.cos(light_angle)
        highlight_y = BASE_RADIUS * light_height * 0.5
        highlight_z = BASE_RADIUS * 0.3 * math.sin(light_angle)
        
        # Multiple highlight layers for realistic reflection
        highlight_layers = [
            {'size': 8.0, 'intensity': 1.0, 'color': (1.0, 1.0, 1.0)},  # Bright core
            {'size': 12.0, 'intensity': 0.6, 'color': (1.0, 0.95, 0.9)}, # Warm glow
            {'size': 16.0, 'intensity': 0.3, 'color': (1.0, 0.9, 0.8)},   # Outer softness
        ]
        
        for layer in highlight_layers:
            size = layer['size']
            intensity = layer['intensity'] * core_intensity * 0.8
            color = layer['color']
            
            # Distance-based fading (simulate sphere curvature)
            distance_fade = 1.0 - min(1.0, math.sqrt(highlight_x**2 + highlight_z**2) / (BASE_RADIUS * 0.5))
            
            final_alpha = intensity * global_intensity * distance_fade * 0.7
            glColor4f(color[0], color[1], color[2], final_alpha)
            glPointSize(size)
            
            glBegin(GL_POINTS)
            glVertex3f(highlight_x, highlight_y, highlight_z)
            glEnd()
        
        # Additional subtle gradient sheen across the sphere
        sheen_segments = 12
        sheen_alpha = 0.15 * core_intensity * global_intensity
        
        glLineWidth(1.0)
        glColor4f(1.0, 0.95, 0.85, sheen_alpha)
        
        # Draw subtle curved lines to suggest sphere surface
        glBegin(GL_LINE_STRIP)
        for i in range(sheen_segments + 1):
            angle = (light_angle + math.pi/4) + (i / float(sheen_segments)) * math.pi/2
            sheen_radius = BASE_RADIUS * 0.8
            
            x = sheen_radius * math.cos(angle) * 0.7
            y = sheen_radius * math.sin(angle * 0.5) * 0.3
            z = sheen_radius * math.sin(angle) * 0.7
            
            # Fade at edges
            edge_fade = math.sin((i / float(sheen_segments)) * math.pi)
            glColor4f(1.0, 0.95, 0.85, sheen_alpha * edge_fade)
            glVertex3f(x, y, z)
        glEnd()
        
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_DEPTH_TEST)

    def _draw_orbit_rings(self, global_intensity, effects):
        """Draw vibrant glowing orbital rings with JARVIS-style red/orange energy."""
        # Superior line rendering for crystal clarity
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glLineWidth(2.0)  # Thicker for vibrant glow effect

        time_s = time.time()
        energy_time = time_s * effects['pulse_speed'] * 0.6

        # Enhanced ring configurations for dynamic motion
        ring_configs = [
            {'radius': BASE_RADIUS * 1.15, 'speed': 0.5, 'alpha_mult': 1.0, 'tilt': 15.0, 'thickness': 2.5, 'color_shift': 0.0},
            {'radius': BASE_RADIUS * 1.5, 'speed': -0.3, 'alpha_mult': 0.85, 'tilt': -10.0, 'thickness': 2.0, 'color_shift': 1.0},
            {'radius': BASE_RADIUS * 1.9, 'speed': 0.2, 'alpha_mult': 0.6, 'tilt': 25.0, 'thickness': 1.5, 'color_shift': 2.0},
        ]

        for i, config in enumerate(ring_configs):
            radius = config['radius']
            speed = config['speed']
            alpha_mult = config['alpha_mult']
            tilt = config['tilt']
            thickness = config['thickness']
            color_shift = config['color_shift']
            
            glPushMatrix()
            
            # Dynamic rotation with varying speeds
            rotation_angle = (energy_time * speed * 12.0) % 360.0
            
            glRotatef(rotation_angle, 0, 1, 0)
            glRotatef(tilt, 1, 0, 0)

            base_alpha = effects['ring_alpha'] * alpha_mult * global_intensity * 1.4

            # Vibrant red/orange color palette for orbital rings
            energy_phase = energy_time + color_shift
            energy_intensity = global_intensity * 1.2
            
            if i == 0:  # Inner ring - bright vibrant orange
                ring_color = (
                    1.0 * energy_intensity,                    # Full red
                    0.6 * energy_intensity,                    # Orange mix
                    0.1 * energy_intensity,                    # Minimal blue for warmth
                    base_alpha * 1.2
                )
            elif i == 1:  # Middle ring - deep red-orange
                ring_color = (
                    0.9 * energy_intensity,
                    0.4 * energy_intensity,
                    0.05 * energy_intensity,
                    base_alpha * 1.0
                )
            else:  # Outer ring - darker red with subtle orange
                ring_color = (
                    0.8 * energy_intensity,
                    0.3 * energy_intensity,
                    0.02 * energy_intensity,
                    base_alpha * 0.8
                )
            
            # Add pulsing energy effect
            pulse = 1.0 + 0.3 * math.sin(energy_phase * 2.0)
            ring_color = (
                min(1.0, ring_color[0] * pulse),
                min(1.0, ring_color[1] * pulse),
                min(1.0, ring_color[2] * pulse),
                ring_color[3]
            )
            
            # Set line thickness for this ring
            glLineWidth(thickness)
            
            # Draw segmented flowing light paths instead of solid rings
            segments_total = 180  # More segments for smoother flow
            segment_length = 8    # Length of each light segment
            segment_gap = 4       # Gap between segments
            flow_speed = energy_time * 2.0 + i * 0.8  # Different flow speeds per ring
            
            glColor4f(*ring_color)
            
            # Draw flowing segments of light
            for start_seg in range(0, segments_total, segment_length + segment_gap):
                # Calculate flow offset for this segment
                flow_offset = (flow_speed + start_seg * 0.1) % segments_total
                
                glBegin(GL_LINE_STRIP)
                for seg_step in range(segment_length):
                    seg_index = (start_seg + seg_step + int(flow_offset)) % segments_total
                    angle = 2.0 * math.pi * (seg_index / float(segments_total))
                    
                    # Segment intensity fades at edges for light trail effect
                    fade_factor = 1.0
                    if seg_step < 2:  # Fade in at start
                        fade_factor = seg_step / 2.0
                    elif seg_step > segment_length - 3:  # Fade out at end
                        fade_factor = (segment_length - seg_step) / 2.0
                    
                    # Apply fade to color
                    segment_color = (
                        ring_color[0] * fade_factor,
                        ring_color[1] * fade_factor,
                        ring_color[2] * fade_factor,
                        ring_color[3] * fade_factor
                    )
                    glColor4f(*segment_color)
                    
                    # Energy flow variation with data-stream feel
                    flow_variation = 1.0 + 0.05 * math.sin(angle * 3.0 + energy_time * 3.0)
                    r = radius * flow_variation
                    
                    x = math.cos(angle) * r
                    z = math.sin(angle) * r
                    y = math.sin(angle * 2.0 + energy_time * 0.8) * 0.02  # Subtle Y variation
                    glVertex3f(x, y, z)
                glEnd()
            
            # Add bright energy nodes that travel along the paths
            node_color = (
                min(1.0, ring_color[0] * 1.8),
                min(1.0, ring_color[1] * 1.8),
                min(1.0, ring_color[2] * 1.8),
                min(1.0, ring_color[3] * 1.5)
            )
            glColor4f(*node_color)
            glPointSize(thickness * 2.0)
            
            # Draw traveling energy nodes
            node_count = 3 + i  # More nodes on outer rings
            glBegin(GL_POINTS)
            for node_idx in range(node_count):
                node_phase = (energy_time * 1.5 + node_idx * (2.0 * math.pi / node_count)) % (2.0 * math.pi)
                node_angle = node_phase
                
                # Node position with slight variation
                node_variation = 1.0 + 0.03 * math.sin(node_angle * 4.0 + energy_time * 2.0)
                r = radius * node_variation
                
                x = math.cos(node_angle) * r
                z = math.sin(node_angle) * r
                y = math.sin(node_angle * 2.0 + energy_time * 0.8) * 0.02
                glVertex3f(x, y, z)
            glEnd()
            
            # Dynamic energy segments with light trails
            if i == 0:  # Only on innermost ring for focus
                # Bright energy trail color
                trail_color = (
                    1.0 * energy_intensity * 1.3,
                    0.8 * energy_intensity * 1.3,
                    0.2 * energy_intensity * 1.3,
                    base_alpha * 1.6
                )
                
                glLineWidth(3.0)  # Thicker for energy trails
                
                # Moving energy segments with fade trails
                for seg in range(3):  # Multiple energy points
                    seg_angle = (energy_time * 1.2 + seg * (2.0 * math.pi / 3)) % (2.0 * math.pi)
                    trail_length = 0.6  # Longer trail for motion effect
                    
                    glBegin(GL_LINE_STRIP)
                    for step in range(20):  # More steps for smoother trails
                        angle = seg_angle + (step / 20.0) * trail_length
                        
                        # Exponential fade for realistic light trails
                        intensity_fade = math.exp(-step * 0.15)
                        
                        trail_color_faded = (
                            trail_color[0] * intensity_fade,
                            trail_color[1] * intensity_fade,
                            trail_color[2] * intensity_fade,
                            trail_color[3] * intensity_fade
                        )
                        glColor4f(*trail_color_faded)
                        
                        # Calculate position on ring with smooth motion
                        x = math.cos(angle) * radius
                        z = math.sin(angle) * radius
                        y = 0.0
                        glVertex3f(x, y, z)
                    glEnd()
            
            glPopMatrix()

        # Reset line width
        glLineWidth(1.0)

    def _draw_floor_grid(self, global_intensity):
        """Draw a very minimal subtle grid beneath the sphere."""
        if self.grid_alpha <= 0.01:  # Skip if too subtle
            return
            
        glEnable(GL_BLEND)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glLineWidth(0.5)

        grid_y = -BASE_RADIUS - 0.8
        grid_extent = BASE_RADIUS * 2.0
        grid_step = BASE_RADIUS * 1.0
        xz_lines = int((grid_extent * 2) / grid_step) + 1

        # Very subtle blue grid
        base_alpha = self.grid_alpha * 0.2  # Even more subtle
        r, g, b = self.energy_color_dim
        color = (r * 0.3, g * 0.3, b * 0.3, base_alpha * global_intensity)

        # Only a few key lines
        glBegin(GL_LINES)
        for i in range(-xz_lines, xz_lines + 1, 2):  # Skip lines for minimal look
            t = (i * grid_step)
            fade = 1.0 - min(1.0, abs(t) / grid_extent)
            fade = fade ** 3.0  # Very dramatic fade
            alpha = base_alpha * fade * 0.3
            if alpha > 0.01:  # Only draw if visible
                glColor4f(color[0], color[1], color[2], alpha)
                glVertex3f(-grid_extent * 0.5, grid_y, t)
                glVertex3f(grid_extent * 0.5, grid_y, t)
                glVertex3f(t, grid_y, -grid_extent * 0.5)
                glVertex3f(t, grid_y, grid_extent * 0.5)
        glEnd()

    def _draw_hud_overlay(self, effects):
        """Draw advanced JARVIS-style targeting reticle with animated brackets."""
        glDisable(GL_DEPTH_TEST)

        # Save matrices
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(-1, 1, -1, 1, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Superior line rendering for crystal clear HUD
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glLineWidth(2.0)  # Thicker for better visibility
        
        current_time = time.time()
        
        # Enhanced dynamic HUD color with better saturation
        hud_color = (0.0, 0.9, 1.0, 0.8)  # Bright cyan for JARVIS
        glColor4f(*hud_color)
        
        # Enhanced central crosshair with gentle pulse
        crosshair_pulse = 0.8 + 0.2 * math.sin(current_time * 1.5)  # Gentle heartbeat
        crosshair_color = (0.0, 0.9 * crosshair_pulse, 1.0 * crosshair_pulse, 0.9)
        glColor4f(*crosshair_color)
        glLineWidth(2.2)
        
        # Main crosshair with breathing animation
        tick_len = 0.035 + 0.008 * math.sin(current_time * 0.8)  # Subtle breathing
        gap = 0.02
        
        glBegin(GL_LINES)
        # Horizontal crosshair
        glVertex2f(gap, 0.0)
        glVertex2f(gap + tick_len, 0.0)
        glVertex2f(-gap, 0.0)
        glVertex2f(-(gap + tick_len), 0.0)
        # Vertical crosshair
        glVertex2f(0.0, gap)
        glVertex2f(0.0, gap + tick_len)
        glVertex2f(0.0, -gap)
        glVertex2f(0.0, -(gap + tick_len))
        glEnd()
        
        # Processing indicator - central dot with intermittent glow
        processing_cycle = (current_time * 2.0) % 3.0  # 3-second processing cycle
        if processing_cycle < 2.0:  # Active processing
            process_intensity = 0.5 + 0.5 * math.sin(processing_cycle * math.pi)
            glColor4f(0.0, 1.0 * process_intensity, 1.0 * process_intensity, 0.8)
            glPointSize(4.0 + 2.0 * process_intensity)
            glBegin(GL_POINTS)
            glVertex2f(0.0, 0.0)
            glEnd()
        
        # Animated targeting brackets with snapping behavior
        snap_cycle = (current_time * 0.4) % 5.0  # 5-second snap cycle
        if snap_cycle < 0.3:  # Snapping in
            snap_progress = snap_cycle / 0.3
            snap_ease = 1.0 - (1.0 - snap_progress) ** 3  # Ease out cubic
            base_distance = 0.25 - 0.10 * snap_ease
            bracket_size = 0.04 + 0.04 * snap_ease
        elif snap_cycle < 4.7:  # Steady state
            base_distance = 0.15
            bracket_size = 0.08
        else:  # Relaxing back
            relax_progress = (snap_cycle - 4.7) / 0.3
            relax_ease = relax_progress ** 2  # Ease in
            base_distance = 0.15 + 0.05 * relax_ease
            bracket_size = 0.08 - 0.02 * relax_ease
        
        # Additional scanning animation
        scan_wave = math.sin(current_time * 2.0)
        scan_distance = base_distance + 0.015 * scan_wave
        bracket_scan = scan_wave  # For compatibility
        bracket_size = bracket_size + 0.01 * bracket_scan
        bracket_size = 0.08 + 0.01 * bracket_scan
        
        # Cyan color for contrast with warm sphere - JARVIS targeting system
        bracket_intensity = 0.7 + 0.3 * math.sin(current_time * 3.0)
        bracket_color = (0.0, 0.9 * bracket_intensity, 1.0 * bracket_intensity, 0.8)
        
        # Lock-on glow effect (triggered periodically)
        lock_on_cycle = (current_time * 0.3) % 4.0  # 4-second cycle
        if lock_on_cycle < 0.2:  # Brief lock-on flash
            lock_glow = math.sin(lock_on_cycle * math.pi / 0.2)
            bracket_color = (
                bracket_color[0] + 0.3 * lock_glow,
                bracket_color[1] + 0.5 * lock_glow,
                bracket_color[2] + 0.7 * lock_glow,
                bracket_color[3] + 0.3 * lock_glow
            )
        
        glColor4f(*bracket_color)
        glLineWidth(2.8)  # Thicker for targeting system
        
        # Advanced corner brackets with scan lines
        corners = [
            (scan_distance, scan_distance),      # Top-right
            (-scan_distance, scan_distance),     # Top-left
            (-scan_distance, -scan_distance),    # Bottom-left
            (scan_distance, -scan_distance)      # Bottom-right
        ]
        
        # Main targeting brackets
        glBegin(GL_LINES)
        for cx, cy in corners:
            # Horizontal bracket line (with scan effect)
            x_dir = bracket_size * (1 if cx > 0 else -1)
            glVertex2f(cx, cy)
            glVertex2f(cx + x_dir, cy)
            
            # Vertical bracket line (with scan effect)
            y_dir = bracket_size * (1 if cy > 0 else -1)
            glVertex2f(cx, cy)
            glVertex2f(cx, cy + y_dir)
            
            # Add scan line extensions during lock-on
            if lock_on_cycle < 0.2:
                scan_extension = 0.03 * lock_glow
                # Extended horizontal line
                glVertex2f(cx + x_dir, cy)
                glVertex2f(cx + x_dir + (scan_extension * (1 if cx > 0 else -1)), cy)
                # Extended vertical line
                glVertex2f(cx, cy + y_dir)
                glVertex2f(cx, cy + y_dir + (scan_extension * (1 if cy > 0 else -1)))
        glEnd()
        
        # Inner precision brackets with independent animation
        inner_scan = math.sin(current_time * 2.5 + math.pi/4)  # Phase offset
        inner_distance = scan_distance * 0.6 + 0.015 * inner_scan
        inner_bracket_size = bracket_size * 0.4
        
        glColor4f(1.0, 1.0, 1.0, 0.6)  # Bright white inner brackets
        glLineWidth(1.8)
        
        glBegin(GL_LINES)
        for cx, cy in corners:
            # Scale to inner position
            inner_cx = cx * 0.6
            inner_cy = cy * 0.6
            
            # Inner bracket with scan movement
            x_dir = inner_bracket_size * (1 if cx > 0 else -1)
            y_dir = inner_bracket_size * (1 if cy > 0 else -1)
            
            glVertex2f(inner_cx, inner_cy)
            glVertex2f(inner_cx + x_dir, inner_cy)
            glVertex2f(inner_cx, inner_cy)
            glVertex2f(inner_cx, inner_cy + y_dir)
        glEnd()
        
        # Target acquisition scanner lines
        if lock_on_cycle < 0.5:  # Scanner active during first half of cycle
            scanner_alpha = 0.4 * (1.0 - lock_on_cycle / 0.5)  # Fade out
            glColor4f(0.2, 1.0, 1.0, scanner_alpha)
            glLineWidth(1.0)
            
            # Horizontal scanner
            scanner_y = math.sin(current_time * 8.0) * 0.12
            glBegin(GL_LINES)
            glVertex2f(-0.2, scanner_y)
            glVertex2f(0.2, scanner_y)
            glEnd()
            
            # Vertical scanner
            scanner_x = math.cos(current_time * 6.0) * 0.12
            glBegin(GL_LINES)
            glVertex2f(scanner_x, -0.2)
            glVertex2f(scanner_x, 0.2)
            glEnd()
        
        # Central targeting circle with scan lines
        glLineWidth(1.2)
        center_color = (0.0, 0.7, 1.0, 0.3)
        glColor4f(*center_color)
        
        # Rotating scan line effect
        scan_rotation = current_time * 2.0
        glBegin(GL_LINE_LOOP)
        inner_radius = 0.06
        segments = 24
        for i in range(segments):
            angle = 2.0 * math.pi * i / segments
            
            # Add scan line intensity variation
            scan_intensity = 1.0 + 0.5 * math.sin(angle + scan_rotation)
            local_radius = inner_radius * scan_intensity
            
            x = local_radius * math.cos(angle)
            y = local_radius * math.sin(angle)
            glVertex2f(x, y)
        glEnd()
        
        # Energy flow indicators (small moving dots)
        glPointSize(3.0)
        dot_color = (0.2, 1.0, 1.0, 0.8)
        glColor4f(*dot_color)
        
        glBegin(GL_POINTS)
        for i in range(4):
            angle = (current_time * 1.5 + i * math.pi / 2) % (2 * math.pi)
            flow_radius = 0.25
            x = math.cos(angle) * flow_radius
            y = math.sin(angle) * flow_radius
            glVertex2f(x, y)
        glEnd()

        # Restore matrices
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

        glEnable(GL_DEPTH_TEST)

    def _draw_surround_hud(self, rms: float):
        """Draw circular HUD ring with J.A.R.V.I.S energy theme."""
        glDisable(GL_DEPTH_TEST)

        # Project to screen-space
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(-1, 1, -1, 1, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glLineWidth(1.2)

        # Energy-themed colors
        r, g, b = self.energy_color_base
        base_r = self.outer_hud_radius
        inner_r = base_r - 0.03
        outer_color = (r * 0.8, g * 0.8, b * 0.8, self.outer_hud_alpha)
        tick_color = (r, g, b, self.outer_hud_tick_alpha)

        # Concentric energy rings
        for ring_r in (inner_r, base_r):
            glColor4f(*outer_color)
            glBegin(GL_LINE_LOOP)
            segments = 128
            for i in range(segments):
                t = 2.0 * math.pi * (i / float(segments))
                glVertex2f(math.cos(t) * ring_r, math.sin(t) * ring_r)
            glEnd()

        # Energy tick marks
        glColor4f(*tick_color)
        glBegin(GL_LINES)
        for deg in range(0, 360, 15):
            t = math.radians(deg)
            r0 = inner_r - (0.02 if deg % 45 != 0 else 0.04)
            r1 = inner_r + 0.01
            glVertex2f(math.cos(t) * r0, math.sin(t) * r0)
            glVertex2f(math.cos(t) * r1, math.sin(t) * r1)
        glEnd()

        # Energy sweep with organic movement
        sweep_len = 0.8 + min(0.4, rms * 2.5)
        sweep_angle = (time.time() * self.outer_hud_sweep_speed * 0.7) % (2.0 * math.pi)
        segments = 48
        glLineWidth(2.0)
        glBegin(GL_LINE_STRIP)
        for i in range(segments + 1):
            t = sweep_angle + sweep_len * (i / float(segments))
            # Energy gradient along sweep
            progress = i / float(segments)
            alpha = self.outer_hud_alpha * (0.1 + 0.9 * progress)
            intensity = 0.6 + 0.4 * progress
            glColor4f(r * intensity, g * intensity, b * intensity, alpha)
            glVertex2f(math.cos(t) * base_r, math.sin(t) * base_r)
        glEnd()

        # Restore matrices
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

        glEnable(GL_DEPTH_TEST)

    def _draw_vignette_overlay(self, effects):
        """JARVIS-style radial vignette with subtle orange/red glow."""
        glDisable(GL_DEPTH_TEST)

        # Save matrices
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(-1, 1, -1, 1, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Enhanced vignette intensity for cinematic effect
        vignette_alpha = effects.get('vignette_alpha', 0.35)
        
        # Subtle red/orange vignette for JARVIS aesthetic
        glBegin(GL_TRIANGLE_FAN)
        # Center transparent
        glColor4f(0.0, 0.0, 0.0, 0.0)
        glVertex2f(0.0, 0.0)
        # Edge with warm cinematic darkness
        steps = 80  # More steps for smoother gradient
        for i in range(steps + 1):
            angle = 2.0 * math.pi * (i / float(steps))
            x = math.cos(angle) * 1.3
            y = math.sin(angle) * 1.3
            
            # Subtle warm edge tint (very dark red/orange)
            edge_r = 0.08 * vignette_alpha  # Very subtle red
            edge_g = 0.02 * vignette_alpha  # Minimal green
            edge_b = 0.0                    # No blue for warmth
            
            glColor4f(edge_r, edge_g, edge_b, vignette_alpha * 0.8)
            glVertex2f(x, y)
        glEnd()

        # Restore matrices
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

        glEnable(GL_DEPTH_TEST)

    def _draw_scanline_overlay(self, effects):
        """Add subtle holographic scan lines across the entire screen."""
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Save matrices
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(-1, 1, -1, 1, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        current_time = time.time()
        
        # Subtle horizontal scan lines
        scan_alpha = 0.03 + 0.01 * math.sin(current_time * 1.2)
        scan_color = (0.0, 0.4, 0.8, scan_alpha)  # Subtle cyan
        
        glColor4f(*scan_color)
        glLineWidth(0.5)
        
        # Draw horizontal scan lines
        line_spacing = 0.08  # Spacing between lines
        scan_offset = (current_time * 0.1) % line_spacing  # Slow moving scan
        
        y = -1.0 - scan_offset
        while y < 1.0:
            # Varying intensity for some lines
            line_intensity = scan_alpha * (0.8 + 0.4 * math.sin(y * 20.0 + current_time))
            if line_intensity > 0.01:
                glColor4f(scan_color[0], scan_color[1], scan_color[2], line_intensity)
                glBegin(GL_LINES)
                glVertex2f(-1.0, y)
                glVertex2f(1.0, y)
                glEnd()
            y += line_spacing
        
        # Occasional bright scan sweep
        sweep_cycle = (current_time * 0.2) % 6.0  # 6-second cycle
        if sweep_cycle < 0.3:  # Brief sweep
            sweep_progress = sweep_cycle / 0.3
            sweep_y = -1.0 + sweep_progress * 2.0
            sweep_alpha = 0.15 * math.sin(sweep_progress * math.pi)
            
            sweep_color = (0.2, 0.8, 1.0, sweep_alpha)
            glColor4f(*sweep_color)
            glLineWidth(2.0)
            
            glBegin(GL_LINES)
            glVertex2f(-1.0, sweep_y)
            glVertex2f(1.0, sweep_y)
            glEnd()
            
            # Sweep glow effect
            for offset in [-0.02, 0.02]:
                glow_alpha = sweep_alpha * 0.3
                glColor4f(sweep_color[0], sweep_color[1], sweep_color[2], glow_alpha)
                glLineWidth(1.0)
                
                glBegin(GL_LINES)
                glVertex2f(-1.0, sweep_y + offset)
                glVertex2f(1.0, sweep_y + offset)
                glEnd()

        # Restore matrices
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

        glEnable(GL_DEPTH_TEST)

    def _draw_background_grid(self, effects):
        """Draw subtle background grid pattern for three-dimensional space feel."""
        glDisable(GL_DEPTH_TEST)
        
        # Save matrices for background rendering
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        
        # Use perspective for 3D grid effect
        aspect = self.width() / self.height() if self.height() > 0 else 1.0
        gluPerspective(45, aspect, 0.1, 100.0)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # Position camera for background grid view
        gluLookAt(0, 0, 5, 0, 0, 0, 0, 1, 0)
        
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glLineWidth(0.5)
        
        current_time = time.time()
        
        # Very subtle grid that slowly moves
        grid_scroll = (current_time * 0.1) % 2.0  # Slow scroll
        grid_alpha = 0.08  # Very subtle
        grid_color = (0.2, 0.4, 0.6, grid_alpha)  # Cool blue-gray
        
        glColor4f(*grid_color)
        
        # Draw far background grid
        glTranslatef(0, 0, -15)  # Push way back
        
        grid_size = 20
        grid_spacing = 1.0
        
        glBegin(GL_LINES)
        # Vertical lines
        for i in range(-grid_size, grid_size + 1):
            x = i * grid_spacing + (grid_scroll - 1.0) * grid_spacing
            glVertex3f(x, -grid_size * grid_spacing, 0)
            glVertex3f(x, grid_size * grid_spacing, 0)
        
        # Horizontal lines
        for i in range(-grid_size, grid_size + 1):
            y = i * grid_spacing + (grid_scroll - 1.0) * grid_spacing
            glVertex3f(-grid_size * grid_spacing, y, 0)
            glVertex3f(grid_size * grid_spacing, y, 0)
        glEnd()
        
        # Add some subtle dots at grid intersections with fading
        glPointSize(1.0)
        dot_color = (0.3, 0.6, 0.8, grid_alpha * 0.8)
        glColor4f(*dot_color)
        
        glBegin(GL_POINTS)
        for i in range(-grid_size//2, grid_size//2 + 1, 2):
            for j in range(-grid_size//2, grid_size//2 + 1, 2):
                x = i * grid_spacing + (grid_scroll - 1.0) * grid_spacing
                y = j * grid_spacing + (grid_scroll - 1.0) * grid_spacing
                
                # Distance-based fading
                distance = math.sqrt(x*x + y*y)
                fade = max(0.0, 1.0 - distance / (grid_size * grid_spacing * 0.8))
                if fade > 0.1:
                    glColor4f(dot_color[0], dot_color[1], dot_color[2], dot_color[3] * fade)
                    glVertex3f(x, y, 0)
        glEnd()
        
        # Restore matrices
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        
        glEnable(GL_DEPTH_TEST)

    def _draw_dashboard(self, rms: float, spec: np.ndarray | None):
        """Minimal modern dashboard overlay with crystal clear text."""
        painter = QtGui.QPainter(self)
        
        # Superior text rendering quality
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        painter.setRenderHint(QtGui.QPainter.TextAntialiasing, True)
        painter.setRenderHint(QtGui.QPainter.HighQualityAntialiasing, True)
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)

        w = self.width()
        h = self.height()
        
        # Only show essential info in top-right corner
        info_width = 200
        info_height = 60
        margin = 20
        info_rect = QtCore.QRect(w - info_width - margin, margin + 40, info_width, info_height)

        # Minimal background
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor.fromRgbF(0.05, 0.08, 0.12, 0.7))
        painter.drawRoundedRect(info_rect, 8, 8)

        # Subtle border
        pen = QtGui.QPen(QtGui.QColor.fromRgbF(0.3, 0.6, 0.9, 0.3))
        pen.setWidthF(1.0)
        painter.setPen(pen)
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.drawRoundedRect(info_rect.adjusted(1, 1, -1, -1), 7, 7)

        # Crystal clear text rendering with enhanced typography
        info_font = typography.get_font('body', 9)
        info_font.setWeight(QtGui.QFont.Normal)
        info_font.setHintingPreference(QtGui.QFont.PreferFullHinting)  # Superior text clarity
        info_font.setStyleStrategy(QtGui.QFont.PreferAntialias)
        painter.setFont(info_font)
        
        # Enhanced text color with better visibility
        text_color = color_scheme.get_color('text_primary', 0.9)
        # Boost text contrast for crystal clarity
        enhanced_color = QtGui.QColor.fromRgbF(
            min(1.0, text_color[0] * 1.1),
            min(1.0, text_color[1] * 1.1),
            min(1.0, text_color[2] * 1.1),
            text_color[3]
        )
        painter.setPen(enhanced_color)
        
        # FPS
        fps_text = f"FPS: {self._fps:0.0f}"
        painter.drawText(info_rect.adjusted(10, 8, -10, -10), Qt.AlignLeft | Qt.AlignTop, fps_text)
        
        # Audio level
        audio_status = "ACTIVE" if self._audio_playing else "IDLE"
        audio_text = f"Audio: {audio_status}"
        painter.drawText(info_rect.adjusted(10, 25, -10, -10), Qt.AlignLeft | Qt.AlignTop, audio_text)
        
        # Processing status
        status_text = f"Status: {self._current_status}"
        painter.drawText(info_rect.adjusted(10, 42, -10, -10), Qt.AlignLeft | Qt.AlignTop, status_text)

        painter.end()
