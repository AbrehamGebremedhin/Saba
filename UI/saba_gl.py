
import time
import math
import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *

from .models import SphereModel, LAT_STEPS, LON_STEPS, BASE_RADIUS
from .audio_analyzer import AudioAnalyzer

FPS_TARGET = 60

class SabaGL(QOpenGLWidget):
    audio_finished = pyqtSignal()

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
        # UI tuning knobs (Saba-style look)
        self.glow_multiplier = 2.2
        self.glow_alpha = 0.10
        self.core_alpha = 0.80
        self.ring_alpha = 0.28
        self.hud_alpha = 0.3
        # Advanced effects
        self.fresnel_strength = 0.7
        self.scan_speed = 0.25
        self.scan_band_width = 0.18  # fraction of sphere radius
        self.vignette_alpha = 0.28
        self.grid_alpha = 0.12
        # Point density controls (uniform, grid-like sampling for cleanliness)
        self.stride_lat_core = 3
        self.stride_lon_core = 3
        self.stride_lat_glow = 2
        self.stride_lon_glow = 2
        self.sample_indices_core = self._build_strided_indices(self.stride_lat_core, self.stride_lon_core)
        self.sample_indices_glow = self._build_strided_indices(self.stride_lat_glow, self.stride_lon_glow)
        # Optional scanline toggle for cleanliness
        self.enable_scanline = False
        # Surround HUD settings
        self.outer_hud_radius = 0.82
        self.outer_hud_alpha = 0.22
        self.outer_hud_tick_alpha = 0.28
        self.outer_hud_sweep_speed = 0.6
        # Track audio playing state
        self._audio_playing = False

    def initializeGL(self):
        glClearColor(0.0, 0.02, 0.05, 1.0)
        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glEnable(GL_PROGRAM_POINT_SIZE)
        glEnable(GL_DEPTH_TEST)
        glHint(GL_POINT_SMOOTH_HINT, GL_NICEST)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, w / max(1.0, h), 0.1, 50.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # 2D background gradient (HUD vibe)
        self._draw_background_gradient()

        # 3D camera setup
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -10.0)
        glRotatef(20, 1, 0, 0)
        glRotatef(self.rotation, 0, 1, 0)

        rms, spec = self.audio.analyze()
        global_intensity = min(1.0, 0.25 + rms * 7.0)

        # Gentle sphere movement and breathing
        if rms > 0.02:
            sway_x = math.sin(time.time() * 0.8) * rms * 0.15
            sway_y = math.cos(time.time() * 0.6) * rms * 0.1
            glTranslatef(sway_x, sway_y, 0.0)
            breath_scale = 1.0 + rms * 0.03
            glScalef(breath_scale, breath_scale, breath_scale)

        # Soft glow halo pass (additive, larger points, depth off)
        self._draw_sphere_points(
            global_intensity,
            spec,
            alpha=self.glow_alpha,
            size_multiplier=self.glow_multiplier,
            depth_test=False,
            with_fresnel=False,
            with_scan=False,
            indices=self.sample_indices_glow,
        )

        # Core crisp point pass (depth on)
        self._draw_sphere_points(
            global_intensity,
            spec,
            alpha=self.core_alpha,
            size_multiplier=0.85,
            depth_test=True,
            with_fresnel=True,
            with_scan=True,
            with_backface_fade=True,
            indices=self.sample_indices_core,
        )

        # Subtle (dashed) orbiting rings around the sphere (3D)
        self._draw_orbit_rings(global_intensity)

        # Faint floor grid beneath sphere (lighter for clarity)
        self._draw_floor_grid(global_intensity)

        # 2D HUD reticle overlay
        self._draw_hud_overlay()

        # Surrounding HUD around the sphere
        self._draw_surround_hud(rms)

        # Soft vignette on top
        self._draw_vignette_overlay()
        # Dashboard overlay (text + meters)
        self._draw_dashboard(rms, spec)

    def load_audio(self, wav_path):
        """Load a new audio file and restart audio analysis."""
        try:
            self.audio = AudioAnalyzer(wav_path)
            # Removed automatic playback - will be triggered manually
            print(f"Loaded new audio file: {wav_path}")
        except Exception as e:
            print(f"Error loading audio file {wav_path}: {e}")

    def play_audio(self):
        """Manually trigger audio playback and emit audio_finished when done."""
        try:
            if self.audio:
                self._audio_playing = True
                def on_audio_done():
                    self._audio_playing = False
                    self.audio_finished.emit()
                QtCore.QTimer.singleShot(300, lambda: self._play_and_emit(on_audio_done))
                print("Audio playback triggered")
        except Exception as e:
            print(f"Error triggering audio playback: {e}")

    def _play_and_emit(self, on_done):
        """Play audio and call on_done when finished."""
        try:
            if self.audio:
                self.audio.play(callback=on_done)
            else:
                on_done()
        except Exception as e:
            print(f"Error in _play_and_emit: {e}")
            on_done()

    def is_audio_playing(self):
        """Return True if audio is currently playing."""
        return self._audio_playing

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
        """Draws a subtle vertical gradient background for a HUD look."""
        glDisable(GL_DEPTH_TEST)

        # Save matrices
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(-1, 1, -1, 1, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glBegin(GL_QUADS)
        # Bottom (darker)
        glColor4f(0.01, 0.03, 0.06, 1.0)
        glVertex2f(-1.0, -1.0)
        glVertex2f(1.0, -1.0)
        # Top (slightly brighter cyan tint)
        glColor4f(0.02, 0.06, 0.10, 1.0)
        glVertex2f(1.0, 1.0)
        glVertex2f(-1.0, 1.0)
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
        """Draw sphere points with given styling. Duplicates sphere displacement for clarity."""
        if depth_test:
            glEnable(GL_DEPTH_TEST)
        else:
            glDisable(GL_DEPTH_TEST)

        # Set a single point size for all points
        if hasattr(self.model.sizes, '__len__') and len(self.model.sizes) > 0:
            avg_size = float(np.sum(self.model.sizes)) / float(len(self.model.sizes))
        else:
            avg_size = 4.0
        # Smaller, crisper points for clarity
        glPointSize(max(1.0, avg_size * size_multiplier * 0.75))

        glBegin(GL_POINTS)
        current_time = time.time()
        slow_time = current_time * 0.15
        # Precompute model rotations used for rim/fresnel
        # Same order as modelview: Ry(self.rotation) then Rx(20)
        rot_y = math.radians(self.rotation)
        cy, sy = math.cos(rot_y), math.sin(rot_y)
        rot_x = math.radians(20.0)
        cx, sx = math.cos(rot_x), math.sin(rot_x)

        # Scanline setup (moves along sphere Y)
        scan_center_y = math.sin(current_time * self.scan_speed) * (BASE_RADIUS * 0.6)
        scan_half_thickness = max(0.001, self.scan_band_width * BASE_RADIUS * 0.5)

        if indices is None:
            indices_iter = range(len(self.model.vertices))
        else:
            indices_iter = indices

        for idx in indices_iter:
            vx, vy, vz = self.model.vertices[idx]
            nx, ny, nz = self.model.normals[idx]
            phase = self.model.phases[idx]
            sensitivity = self.model.sensitivity[idx]

            band_value = 0.0
            if spec is not None:
                latitude_band = int(((ny + 1.0) * 0.5) * LAT_STEPS)
                band_value = spec[min(len(spec) - 1, latitude_band)]

            base_displacement = math.sin(phase + slow_time) * 0.004
            audio_response = sensitivity * band_value * 0.12
            displacement = base_displacement + audio_response

            px = vx + nx * displacement
            py = vy + ny * displacement
            pz = vz + nz * displacement

            intensity = global_intensity * (0.7 + 0.3 * sensitivity)

            # Fresnel rim lighting and backface fade based on view-space normal z
            view_nz = 0.0
            if with_fresnel or with_backface_fade:
                # Apply model rotations to normal: n' = Rx * Ry * n
                # First Ry
                ny_z = nz
                nxp = nx * cy + nz * -sy
                nzp = nx * sy + ny_z * cy
                nyp = ny
                # Then Rx
                nxx = nxp
                nyy = nyp * cx - nzp * sx
                nzz = nyp * sx + nzp * cx
                view_nz = nzz
                if with_fresnel:
                    fresnel = max(0.0, 1.0 - abs(view_nz))
                    intensity += self.fresnel_strength * (fresnel ** 1.5) * 0.6

            # Vertical scanline boost (reduced to avoid fuzz)
            if with_scan and getattr(self, 'enable_scanline', True):
                dy = abs(vy - scan_center_y)
                if dy < scan_half_thickness:
                    t = 1.0 - (dy / scan_half_thickness)
                    intensity += 0.22 * (t ** 2)

            final_alpha = alpha
            if with_backface_fade:
                # Fade back faces to reduce visual clutter. Assume view faces have negative z.
                facing = max(0.0, 0.5 + 0.5 * (-view_nz))
                final_alpha *= 0.6 + 0.4 * facing

            glColor4f(0.2 * intensity, 0.6 * intensity, 1.0 * intensity, final_alpha)
            glVertex3f(px, py, pz)
        glEnd()

        # Restore depth test for subsequent draws
        glEnable(GL_DEPTH_TEST)

    def _draw_orbit_rings(self, global_intensity):
        """Draw subtle rotating rings around the sphere for a Saba vibe (dashed)."""
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glLineWidth(1.25)

        intensity = global_intensity
        ring_color = (0.2 * intensity, 0.7 * intensity, 1.0 * intensity, self.ring_alpha)

        # Draw rings in three orientations
        ring_radii = [BASE_RADIUS * r for r in (1.04, 1.20, 1.38)]
        time_s = time.time()

        for i, radius in enumerate(ring_radii):
            glPushMatrix()
            # Distinct slow rotations per ring
            glRotatef((time_s * (4.0 + i * 2.0)) % 360.0, 0, 1, 0)
            glRotatef(15.0 + i * 10.0, 1, 0, 0)

            glColor4f(*ring_color)
            segments = 220
            dash = 12
            gap = 8
            step = 2.0 * math.pi / float(segments)
            # Build dashed arcs
            s = 0
            while s < segments:
                # Draw dash
                glBegin(GL_LINE_STRIP)
                for k in range(dash):
                    idx = s + k
                    if idx >= segments:
                        break
                    angle = step * idx
                    x = math.cos(angle) * radius
                    z = math.sin(angle) * radius
                    glVertex3f(x, 0.0, z)
                glEnd()
                s += dash + gap
            glPopMatrix()

        glLineWidth(1.0)

    def _draw_floor_grid(self, global_intensity):
        """Draw a faint grid under the sphere to ground the composition."""
        glEnable(GL_BLEND)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glLineWidth(1.0)

        grid_y = -BASE_RADIUS - 0.25
        grid_extent = BASE_RADIUS * 2.5
        grid_step = BASE_RADIUS * 0.4
        xz_lines = int((grid_extent * 2) / grid_step) + 1

        base = max(0.05, self.grid_alpha * 0.9)
        color = (0.2 * global_intensity, 0.6 * global_intensity, 1.0 * global_intensity, base)
        glColor4f(*color)

        # X lines
        glBegin(GL_LINES)
        for i in range(-xz_lines, xz_lines + 1):
            t = (i * grid_step)
            fade = 1.0 - min(1.0, abs(t) / grid_extent)
            glColor4f(color[0], color[1], color[2], base * fade)
            glVertex3f(-grid_extent, grid_y, t)
            glVertex3f(grid_extent, grid_y, t)
        glEnd()

        # Z lines
        glBegin(GL_LINES)
        for i in range(-xz_lines, xz_lines + 1):
            t = (i * grid_step)
            fade = 1.0 - min(1.0, abs(t) / grid_extent)
            glColor4f(color[0], color[1], color[2], base * fade)
            glVertex3f(t, grid_y, -grid_extent)
            glVertex3f(t, grid_y, grid_extent)
        glEnd()

    def _draw_hud_overlay(self):
        """Draw a minimal 2D reticle overlay at the center of the screen."""
        glDisable(GL_DEPTH_TEST)

        # Save matrices
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(-1, 1, -1, 1, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Reticle circle
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glLineWidth(1.0)
        glColor4f(0.2, 0.7, 1.0, self.hud_alpha)
        radius = 0.08
        segments = 96
        glBegin(GL_LINE_LOOP)
        for i in range(segments):
            t = 2.0 * math.pi * (i / float(segments))
            glVertex2f(math.cos(t) * radius, math.sin(t) * radius)
        glEnd()

        # Crosshair ticks
        tick_len = 0.025
        gap = 0.015
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
        """Draw a circular HUD ring around the sphere with ticks, arcs and a rotating sweep."""
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

        # Outer ring base
        base_r = self.outer_hud_radius
        inner_r = base_r - 0.02
        outer_color = (0.2, 0.7, 1.0, self.outer_hud_alpha)
        tick_color = (0.2, 0.7, 1.0, self.outer_hud_tick_alpha)

        # Thin concentric double ring
        for r in (inner_r, base_r):
            glColor4f(*outer_color)
            glBegin(GL_LINE_LOOP)
            segments = 160
            for i in range(segments):
                t = 2.0 * math.pi * (i / float(segments))
                glVertex2f(math.cos(t) * r, math.sin(t) * r)
            glEnd()

        # Radial ticks every 15 degrees
        glColor4f(*tick_color)
        glBegin(GL_LINES)
        for deg in range(0, 360, 15):
            t = math.radians(deg)
            r0 = inner_r - 0.015 if deg % 45 != 0 else inner_r - 0.03
            r1 = inner_r + 0.008
            glVertex2f(math.cos(t) * r0, math.sin(t) * r0)
            glVertex2f(math.cos(t) * r1, math.sin(t) * r1)
        glEnd()

        # Rotating sweep arc (audio-reactive length)
        sweep_len = 0.60 + min(0.35, rms * 2.0)
        sweep_angle = (time.time() * self.outer_hud_sweep_speed) % (2.0 * math.pi)
        segments = 48
        glBegin(GL_LINE_STRIP)
        for i in range(segments + 1):
            t = sweep_angle + sweep_len * (i / float(segments))
            # Gradient alpha along sweep
            a = self.outer_hud_alpha * (0.2 + 0.8 * (i / float(segments)))
            glColor4f(0.2, 0.7, 1.0, a)
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
        """Qt-painter-based dashboard at the bottom: FPS, RMS meter, and spectrum bars."""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        margin = int(min(w, h) * 0.03)
        panel_h = int(h * 0.16)
        panel_rect = QtCore.QRect(margin, h - panel_h - margin, w - 2 * margin, panel_h)

        # Panel background
        bg_color = QtGui.QColor.fromRgbF(0.01, 0.03, 0.06, 0.75)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(bg_color)
        painter.drawRoundedRect(panel_rect, 12, 12)

        # Border
        pen = QtGui.QPen(QtGui.QColor.fromRgbF(0.15, 0.55, 0.95, 0.35))
        pen.setWidthF(1.4)
        painter.setPen(pen)
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.drawRoundedRect(panel_rect.adjusted(1, 1, -1, -1), 12, 12)

        # Title
        title_font = QtGui.QFont("Segoe UI", max(9, int(h * 0.018)), QtGui.QFont.DemiBold)
        painter.setFont(title_font)
        painter.setPen(QtGui.QColor.fromRgbF(0.55, 0.85, 1.0, 0.8))
        painter.drawText(panel_rect.adjusted(14, 8, -14, -8), QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop, "Saba DASHBOARD")

        # FPS
        info_font = QtGui.QFont("Segoe UI", max(8, int(h * 0.016)))
        painter.setFont(info_font)
        painter.setPen(QtGui.QColor.fromRgbF(0.7, 0.9, 1.0, 0.9))
        fps_text = f"FPS: {self._fps:0.1f}"
        painter.drawText(panel_rect.adjusted(14, 32, -14, -8), QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop, fps_text)

        # RMS meter
        meter_w = int(panel_rect.width() * 0.28)
        meter_h = int(panel_rect.height() * 0.28)
        meter_rect = QtCore.QRect(panel_rect.left() + 14, panel_rect.top() + 56, meter_w, meter_h)
        painter.setPen(QtGui.QColor.fromRgbF(0.2, 0.7, 1.0, 0.35))
        painter.setBrush(QtGui.QColor.fromRgbF(0.02, 0.08, 0.12, 0.8))
        painter.drawRoundedRect(meter_rect, 6, 6)
        level = max(0.0, min(1.0, rms * 3.0))
        fill_rect = QtCore.QRect(meter_rect.left() + 2, meter_rect.top() + 2, int((meter_rect.width() - 4) * level), meter_rect.height() - 4)
        grad = QtGui.QLinearGradient(fill_rect.topLeft(), fill_rect.topRight())
        grad.setColorAt(0.0, QtGui.QColor.fromRgbF(0.15, 0.55, 1.0, 0.9))
        grad.setColorAt(1.0, QtGui.QColor.fromRgbF(0.25, 0.9, 1.0, 0.9))
        painter.setBrush(QtGui.QBrush(grad))
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRoundedRect(fill_rect, 6, 6)
        painter.setPen(QtGui.QColor.fromRgbF(0.55, 0.85, 1.0, 0.8))
        painter.drawText(meter_rect.adjusted(6, 0, -6, 0), QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, "RMS")

        # Spectrum bars (16 bands)
        bands = 16
        spec_vals = np.zeros(bands, dtype=np.float32)
        if spec is not None and spec.size > 0:
            step = int(max(1, len(spec) / bands))
            for i in range(bands):
                i0 = i * step
                i1 = min(len(spec), (i + 1) * step)
                if i0 < i1:
                    spec_vals[i] = float(np.mean(spec[i0:i1]))
            # Normalize
            m = float(np.max(spec_vals))
            if m > 1e-6:
                spec_vals /= m

        bars_left = meter_rect.right() + 24
        bars_top = meter_rect.top()
        bars_w = panel_rect.right() - 14 - bars_left
        bars_h = meter_h
        bar_gap = 6
        bar_w = max(2, int((bars_w - (bands - 1) * bar_gap) / bands))
        for i in range(bands):
            x = bars_left + i * (bar_w + bar_gap)
            val = float(spec_vals[i])
            bh = int(bars_h * val)
            rect = QtCore.QRect(x, bars_top + (bars_h - bh), bar_w, bh)
            grad = QtGui.QLinearGradient(rect.bottomLeft(), rect.topLeft())
            grad.setColorAt(0.0, QtGui.QColor.fromRgbF(0.05, 0.2, 0.35, 0.6))
            grad.setColorAt(1.0, QtGui.QColor.fromRgbF(0.2, 0.8, 1.0, 0.95))
            painter.setBrush(QtGui.QBrush(grad))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawRoundedRect(rect, 3, 3)

        painter.end()
