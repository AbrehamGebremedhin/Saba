
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
        # Removed automatic audio playback - will be triggered manually via play() method
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_scene)
        self.timer.start(int(1000 / FPS_TARGET))
        # UI tuning knobs - J.A.R.V.I.S movie style (orange/golden energy)
        self.glow_multiplier = 4.0  # Much larger glow for energy effect
        self.glow_alpha = 0.25
        self.core_alpha = 0.95
        self.ring_alpha = 0.45
        self.hud_alpha = 0.35
        # Advanced effects - J.A.R.V.I.S style
        self.fresnel_strength = 2.0  # Stronger rim lighting
        self.scan_speed = 0.15  # Slower, more organic movement
        self.scan_band_width = 0.35  # Wider energy bands
        self.vignette_alpha = 0.32
        self.grid_alpha = 0.18
        # Energy colors - Orange/golden like the movie
        self.energy_color_base = (1.0, 0.6, 0.2)  # Orange base
        self.energy_color_bright = (1.0, 0.9, 0.4)  # Golden bright
        self.energy_color_dim = (0.8, 0.3, 0.1)  # Deep orange
        # Point density controls (uniform, grid-like sampling for cleanliness)
        self.stride_lat_core = 2  # Increased density
        self.stride_lon_core = 2
        self.stride_lat_glow = 1  # Even more dense for glow
        self.stride_lon_glow = 2
        self.sample_indices_core = self._build_strided_indices(self.stride_lat_core, self.stride_lon_core)
        self.sample_indices_glow = self._build_strided_indices(self.stride_lat_glow, self.stride_lon_glow)
        # Optional scanline toggle for cleanliness
        self.enable_scanline = True
        # Surround HUD settings - Enhanced
        self.outer_hud_radius = 0.85
        self.outer_hud_alpha = 0.28
        self.outer_hud_tick_alpha = 0.32
        self.outer_hud_sweep_speed = 0.8
        # Track audio playing state
        self._audio_playing = False
        # Status tracking
        self._current_status = "Standby"
        # Enhanced sphere effects - modern and clean
        self.sphere_breathing = True
        self.particle_trails = False  # Disable for cleaner look
        self.energy_pulses = True
        self.holographic_distortion = False  # Disable for cleaner look
        
        # JARVIS-style cinematic color scheme
        self.energy_color_base = (0.2, 0.8, 1.0)  # Bright cyan-blue
        self.energy_color_bright = (0.4, 0.9, 1.0)  # Bright cyan
        self.energy_color_dim = (0.1, 0.5, 0.9)  # Deep blue
        
        # More cinematic visual parameters with better visibility
        self.glow_multiplier = 2.8  # Increased glow visibility
        self.glow_alpha = 0.4  # Much more visible glow
        self.core_alpha = 0.95  # Very visible core
        self.ring_alpha = 0.6  # More visible rings
        self.hud_alpha = 0.25
        self.vignette_alpha = 0.08  # Very subtle vignette
        self.grid_alpha = 0.02  # Almost invisible grid
        
        # Smoother, more organic movement
        self.fresnel_strength = 1.5
        self.scan_speed = 0.05  # Very slow, organic scanning
        self.scan_band_width = 0.15
        
        # Emit initial status
        self.status_update.emit("Interface Initialized", False)

    def initializeGL(self):
        # Modern dark space background
        glClearColor(0.02, 0.03, 0.05, 1.0)
        
        # Enhanced point rendering for modern look
        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_PROGRAM_POINT_SIZE)
        glEnable(GL_DEPTH_TEST)
        glHint(GL_POINT_SMOOTH_HINT, GL_NICEST)
        
        # Enhanced line rendering
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        
        # Multi-sampling for better quality (if available)
        glEnable(GL_MULTISAMPLE)
        
        # Enhanced depth testing
        glDepthFunc(GL_LEQUAL)
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, w / max(1.0, h), 0.1, 50.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Enhanced background with more atmosphere
        self._draw_background_gradient()

        # 3D camera setup
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -10.0)
        glRotatef(20, 1, 0, 0)
        glRotatef(self.rotation, 0, 1, 0)

        rms, spec = self.audio.analyze()
        global_intensity = min(1.0, 0.6 + rms * 5.0)  # Higher base intensity for visibility
        
        # Add processing intensity boost when thinking
        if self._current_status == "Processing":
            global_intensity = max(global_intensity, 0.8 + math.sin(time.time() * 4.0) * 0.2)

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

        # Enhanced multi-pass rendering for highly visible JARVIS-style sphere
        
        # Pass 1: Strong outer glow for visibility and depth
        self._draw_sphere_points(
            global_intensity,
            spec,
            alpha=self.glow_alpha * 0.8,
            size_multiplier=self.glow_multiplier * 1.3,
            depth_test=False,
            with_fresnel=False,
            with_scan=False,
            indices=self.sample_indices_glow,
        )

        # Pass 2: Main sphere with strong visibility
        self._draw_sphere_points(
            global_intensity,
            spec,
            alpha=self.core_alpha,
            size_multiplier=1.2,  # Slightly larger points
            depth_test=True,
            with_fresnel=True,
            with_scan=True,
            with_backface_fade=True,
            indices=self.sample_indices_core,
        )
        
        # Pass 3: Bright inner core for energy center
        self._draw_sphere_points(
            global_intensity,
            spec,
            alpha=min(1.0, self.core_alpha * 1.1),
            size_multiplier=0.6,
            depth_test=True,
            with_fresnel=False,
            with_scan=True,
            indices=self.sample_indices_core,
        )

        # Enhanced orbiting rings with cleaner look
        self._draw_orbit_rings(global_intensity)

        # Minimal HUD elements
        self._draw_hud_overlay()

        # Subtle vignette for cinematic effect
        self._draw_vignette_overlay()

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
            self.status_update.emit("Processing Input", True)
            # Increase scan speed and intensity when thinking
            self.scan_speed = 0.8
            self.fresnel_strength = 2.0
        else:
            self._current_status = "Standby"
            self.status_update.emit("Standby", False)
            # Return to normal visual parameters
            self.scan_speed = 0.35
            self.fresnel_strength = 1.2

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
        """Modern clean gradient background."""
        glDisable(GL_DEPTH_TEST)

        # Save matrices
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(-1, 1, -1, 1, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Modern gradient background
        glBegin(GL_QUADS)
        # Bottom (dark blue-black)
        glColor4f(0.02, 0.03, 0.06, 1.0)
        glVertex2f(-1.0, -1.0)
        glVertex2f(1.0, -1.0)
        # Top (slightly lighter blue-black)
        glColor4f(0.04, 0.06, 0.10, 1.0)
        glVertex2f(1.0, 1.0)
        glVertex2f(-1.0, 1.0)
        glEnd()
        
        # Subtle center glow (much more subtle than before)
        glBegin(GL_TRIANGLE_FAN)
        # Center with very faint blue glow
        glColor4f(0.05, 0.10, 0.15, 0.08)
        glVertex2f(0.0, 0.0)
        # Edge completely dark
        steps = 32
        for i in range(steps + 1):
            angle = 2.0 * math.pi * (i / float(steps))
            x = math.cos(angle) * 1.2
            y = math.sin(angle) * 1.2
            glColor4f(0.02, 0.03, 0.05, 0.0)
            glVertex2f(x, y)
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

    def _draw_sphere_points(self, global_intensity, spec, alpha=0.9, size_multiplier=1.0, depth_test=True, with_fresnel=False, with_scan=False, with_backface_fade=False, indices=None):
        """Draw sphere points with J.A.R.V.I.S movie-style organic energy patterns."""
        if depth_test:
            glEnable(GL_DEPTH_TEST)
        else:
            glDisable(GL_DEPTH_TEST)

        # Dynamic point size based on energy intensity
        if hasattr(self.model.sizes, '__len__') and len(self.model.sizes) > 0:
            avg_size = float(np.sum(self.model.sizes)) / float(len(self.model.sizes))
        else:
            avg_size = 4.0
        
        # Larger, more organic points
        base_size = max(2.0, avg_size * size_multiplier * 1.2)
        glPointSize(base_size)

        glBegin(GL_POINTS)
        current_time = time.time()
        
        # Slower, more organic time for flowing patterns
        flow_time = current_time * 0.08
        energy_time = current_time * 0.25
        
        # Create organic flow patterns
        wave_phase1 = math.sin(energy_time * 0.7) * 2.0
        wave_phase2 = math.cos(energy_time * 0.5) * 1.8
        wave_phase3 = math.sin(energy_time * 1.2) * 1.5
        
        # Model rotations for fresnel/backface calculations
        rot_y = math.radians(self.rotation)
        cy, sy = math.cos(rot_y), math.sin(rot_y)
        rot_x = math.radians(20.0)
        cx, sx = math.cos(rot_x), math.sin(rot_x)

        # Energy flow center that moves organically
        flow_center_x = math.sin(energy_time * 0.3) * 0.8
        flow_center_y = math.cos(energy_time * 0.4) * 0.6
        flow_center_z = math.sin(energy_time * 0.35) * 0.7

        if indices is None:
            indices_iter = range(len(self.model.vertices))
        else:
            indices_iter = indices

        for idx in indices_iter:
            vx, vy, vz = self.model.vertices[idx]
            nx, ny, nz = self.model.normals[idx]
            phase = self.model.phases[idx]
            sensitivity = self.model.sensitivity[idx]

            # Organic energy flow calculation
            # Distance from flowing energy centers
            dist_to_flow = math.sqrt(
                (vx - flow_center_x)**2 + 
                (vy - flow_center_y)**2 + 
                (vz - flow_center_z)**2
            ) / BASE_RADIUS
            
            # Multiple overlapping wave patterns for organic look
            wave1 = math.sin(phase + flow_time * 3.0 + wave_phase1)
            wave2 = math.cos(phase * 1.7 + flow_time * 2.3 + wave_phase2)
            wave3 = math.sin(phase * 0.8 + flow_time * 1.8 + wave_phase3)
            
            # Combine waves for organic displacement
            organic_pattern = (wave1 + wave2 * 0.7 + wave3 * 0.5) / 3.0
            
            # Energy flow effect - points closer to flow center are brighter
            flow_intensity = max(0.2, 1.0 - dist_to_flow * 0.8)
            flow_displacement = organic_pattern * 0.08 * flow_intensity
            
            # Audio response
            band_value = 0.0
            if spec is not None:
                latitude_band = int(((ny + 1.0) * 0.5) * len(spec))
                band_value = spec[min(len(spec) - 1, latitude_band)] if latitude_band < len(spec) else 0.0

            # Total displacement with audio response
            audio_displacement = sensitivity * band_value * 0.15
            total_displacement = flow_displacement + audio_displacement
            
            # Apply displacement
            px = vx + nx * total_displacement
            py = vy + ny * total_displacement
            pz = vz + nz * total_displacement

            # Energy intensity calculation
            base_intensity = global_intensity * (0.4 + 0.6 * sensitivity)
            flow_boost = flow_intensity * 0.6
            audio_boost = audio_displacement * 3.0
            
            intensity = min(1.0, base_intensity + flow_boost + audio_boost)

            # Fresnel rim lighting for energy edge effect
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
                    intensity += self.fresnel_strength * (fresnel ** 1.8) * flow_intensity

            # Energy band scanning (slower, more organic)
            if with_scan:
                scan_center_y = math.sin(current_time * self.scan_speed * 0.7) * (BASE_RADIUS * 0.8)
                scan_thickness = self.scan_band_width * BASE_RADIUS * 0.6
                dy = abs(vy - scan_center_y)
                if dy < scan_thickness:
                    scan_factor = 1.0 - (dy / scan_thickness)
                    intensity += 0.4 * (scan_factor ** 1.5) * flow_intensity

            # J.A.R.V.I.S orange/golden color scheme
            # Base color depends on energy intensity and position
            energy_mix = intensity * flow_intensity
            
            if energy_mix > 0.7:  # Bright energy - golden
                r, g, b = self.energy_color_bright
                color_alpha = alpha * min(1.0, energy_mix)
            elif energy_mix > 0.3:  # Medium energy - orange
                r, g, b = self.energy_color_base
                color_alpha = alpha * energy_mix
            else:  # Low energy - deep orange
                r, g, b = self.energy_color_dim
                color_alpha = alpha * energy_mix * 0.8
            
            # Add some variation based on position for organic look
            pos_variation = (math.sin(vx * 0.5) + math.cos(vy * 0.7) + math.sin(vz * 0.6)) / 3.0
            r += pos_variation * 0.1 * flow_intensity
            g += pos_variation * 0.05 * flow_intensity
            b += pos_variation * 0.02 * flow_intensity
            
            # Clamp colors
            r = max(0.0, min(1.0, r))
            g = max(0.0, min(1.0, g))
            b = max(0.0, min(1.0, b))

            # Backface fading for depth
            final_alpha = color_alpha
            if with_backface_fade and view_nz != 0.0:
                facing = max(0.0, 0.3 + 0.7 * (-view_nz))
                final_alpha *= 0.4 + 0.6 * facing

            glColor4f(r * intensity, g * intensity, b * intensity, final_alpha)
            glVertex3f(px, py, pz)
            
        glEnd()
        glEnable(GL_DEPTH_TEST)

    def _draw_orbit_rings(self, global_intensity):
        """Draw minimal modern energy rings."""
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glLineWidth(1.0)

        time_s = time.time()
        energy_time = time_s * 0.2

        # Only two rings but more visible
        ring_configs = [
            {'radius': BASE_RADIUS * 1.2, 'speed': 0.5, 'alpha_mult': 1.0},
            {'radius': BASE_RADIUS * 1.6, 'speed': 0.3, 'alpha_mult': 0.7},
        ]

        for i, config in enumerate(ring_configs):
            radius = config['radius']
            speed = config['speed']
            alpha_mult = config['alpha_mult']
            
            glPushMatrix()
            
            rotation_angle = (energy_time * speed * 10.0) % 360.0
            tilt_x = 15.0
            
            glRotatef(rotation_angle, 0, 1, 0)
            glRotatef(tilt_x, 1, 0, 0)

            base_alpha = self.ring_alpha * alpha_mult * global_intensity

            # Draw visible ring
            segments = 80
            glColor4f(*self.energy_color_base, base_alpha)
            
            glBegin(GL_LINE_LOOP)
            for s in range(segments):
                angle = 2.0 * math.pi * (s / float(segments))
                x = math.cos(angle) * radius
                z = math.sin(angle) * radius
                y = 0.0
                glVertex3f(x, y, z)
            glEnd()
                
            glPopMatrix()

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

    def _draw_hud_overlay(self):
        """Draw minimal modern HUD reticle."""
        glDisable(GL_DEPTH_TEST)

        # Save matrices
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(-1, 1, -1, 1, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Minimal reticle
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glLineWidth(1.0)
        
        # Modern blue/cyan color
        r, g, b = self.energy_color_base
        glColor4f(r * 0.8, g * 0.8, b * 0.8, self.hud_alpha)
        
        # Simple crosshair - smaller and more subtle
        tick_len = 0.015
        gap = 0.008
        glBegin(GL_LINES)
        # Right
        glVertex2f(gap, 0.0)
        glVertex2f(gap + tick_len, 0.0)
        # Left
        glVertex2f(-gap, 0.0)
        glVertex2f(-(gap + tick_len), 0.0)
        # Up
        glVertex2f(0.0, gap)
        glVertex2f(0.0, gap + tick_len)
        # Down
        glVertex2f(0.0, -gap)
        glVertex2f(0.0, -(gap + tick_len))
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

    def _draw_vignette_overlay(self):
        """Soft radial darkening towards edges for cinematic look."""
        glDisable(GL_DEPTH_TEST)

        # Save matrices
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(-1, 1, -1, 1, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glBegin(GL_TRIANGLE_FAN)
        # Center transparent
        glColor4f(0.0, 0.0, 0.0, 0.0)
        glVertex2f(0.0, 0.0)
        # Edge dark
        steps = 64
        for i in range(steps + 1):
            angle = 2.0 * math.pi * (i / float(steps))
            x = math.cos(angle)
            y = math.sin(angle)
            glColor4f(0.0, 0.0, 0.0, self.vignette_alpha)
            glVertex2f(x, y)
        glEnd()

        # Restore matrices
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

        glEnable(GL_DEPTH_TEST)

    def _draw_dashboard(self, rms: float, spec: np.ndarray | None):
        """Minimal modern dashboard overlay."""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

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

        # Minimal text info
        info_font = QtGui.QFont("Segoe UI", 9)
        painter.setFont(info_font)
        painter.setPen(QtGui.QColor.fromRgbF(0.8, 0.9, 1.0, 0.8))
        
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
