"""
Advanced JARVIS-style Color Scheme and Visual Effects System
Implements the sophisticated color palette and visual effects described in the requirements.
"""

import math
import time
from typing import Tuple, Dict, Any
from dataclasses import dataclass

@dataclass
class ColorPalette:
    """Defines color palettes for different UI states and elements"""
    # Primary Palette - Oranges/Golds
    energy_base: Tuple[float, float, float] = (1.0, 0.6, 0.2)      # Deep orange
    energy_bright: Tuple[float, float, float] = (1.0, 0.9, 0.4)    # Warm gold
    energy_hot: Tuple[float, float, float] = (1.0, 0.8, 0.3)       # Bright orange-gold
    
    # Deep Reds for alerts and high activity
    alert_base: Tuple[float, float, float] = (0.9, 0.3, 0.2)       # Deep red
    alert_bright: Tuple[float, float, float] = (1.0, 0.4, 0.3)     # Bright red-orange
    warning: Tuple[float, float, float] = (1.0, 0.5, 0.1)          # Orange-red warning
    
    # Cool Blues/Cyans for contrast and information
    info_base: Tuple[float, float, float] = (0.3, 0.7, 1.0)        # Bright blue
    info_bright: Tuple[float, float, float] = (0.5, 0.9, 1.0)      # Bright cyan
    info_dim: Tuple[float, float, float] = (0.2, 0.5, 0.8)         # Darker blue
    
    # Background and UI elements
    bg_dark: Tuple[float, float, float] = (0.02, 0.03, 0.05)       # Very dark blue-black
    bg_medium: Tuple[float, float, float] = (0.05, 0.08, 0.12)     # Dark blue-gray
    bg_transparent_blue: Tuple[float, float, float, float] = (0.02, 0.15, 0.25, 0.85)  # Translucent blue
    bg_transparent_dark: Tuple[float, float, float, float] = (0.01, 0.03, 0.06, 0.9)   # Translucent dark
    
    # Text colors
    text_primary: Tuple[float, float, float] = (0.9, 0.95, 1.0)    # Bright white-blue
    text_secondary: Tuple[float, float, float] = (0.7, 0.8, 0.9)   # Medium blue-white
    text_dim: Tuple[float, float, float] = (0.5, 0.6, 0.7)         # Dimmed blue-white

class JARVISColorScheme:
    """
    Advanced JARVIS-style color scheme manager with dynamic color transitions
    and context-aware color selection based on system state.
    """
    
    def __init__(self):
        self.palette = ColorPalette()
        self._current_mode = "standby"
        self._transition_start_time = 0.0
        self._transition_duration = 1.0
        self._previous_colors = {}
        
        # Visual effect parameters
        self.holographic_settings = {
            'glow_intensity': 4.0,
            'glow_alpha': 0.3,
            'core_alpha': 0.95,
            'ring_alpha': 0.6,
            'fresnel_strength': 2.0,
            'scan_speed': 0.12,
            'scan_width': 0.35,
            'pulse_speed': 0.8,
            'vignette_alpha': 0.25
        }
        
        # Typography settings
        self.typography = {
            'primary_family': 'Orbitron',
            'secondary_family': 'Rajdhani',
            'fallback_family': 'Segoe UI',
            'mono_family': 'Consolas',
            'size_large': 24,
            'size_medium': 16,
            'size_small': 12,
            'size_tiny': 10,
            'weight_bold': 700,
            'weight_medium': 500,
            'weight_light': 300,
            'letter_spacing': 2
        }
    
    def set_mode(self, mode: str, transition_time: float = 1.0):
        """
        Set the current system mode and trigger smooth color transitions.
        
        Args:
            mode: One of 'standby', 'listening', 'processing', 'alert', 'active'
            transition_time: Duration of color transition in seconds
        """
        if mode != self._current_mode:
            self._previous_colors = self._get_current_colors()
            self._current_mode = mode
            self._transition_start_time = time.time()
            self._transition_duration = transition_time
    
    def get_mode(self) -> str:
        """Get the current system mode."""
        return self._current_mode
    
    def _get_transition_progress(self) -> float:
        """Calculate transition progress (0.0 to 1.0)."""
        if self._transition_duration <= 0:
            return 1.0
        
        elapsed = time.time() - self._transition_start_time
        return min(1.0, elapsed / self._transition_duration)
    
    def _ease_in_out_cubic(self, t: float) -> float:
        """Smooth easing function for transitions."""
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2
    
    def _interpolate_color(self, color1: Tuple[float, ...], color2: Tuple[float, ...], t: float) -> Tuple[float, ...]:
        """Smoothly interpolate between two colors."""
        eased_t = self._ease_in_out_cubic(t)
        return tuple(c1 + (c2 - c1) * eased_t for c1, c2 in zip(color1, color2))
    
    def _get_current_colors(self) -> Dict[str, Tuple[float, ...]]:
        """Get current colors based on system mode."""
        colors = {}
        
        if self._current_mode == "standby":
            colors.update({
                'primary': self.palette.info_base,
                'secondary': self.palette.info_dim,
                'accent': self.palette.energy_base,
                'glow': self.palette.info_bright,
                'background': self.palette.bg_dark
            })
            
        elif self._current_mode == "listening":
            colors.update({
                'primary': self.palette.energy_base,
                'secondary': self.palette.energy_hot,
                'accent': self.palette.energy_bright,
                'glow': self.palette.energy_bright,
                'background': self.palette.bg_dark
            })
            
        elif self._current_mode == "processing":
            colors.update({
                'primary': self.palette.energy_bright,
                'secondary': self.palette.energy_hot,
                'accent': self.palette.warning,
                'glow': self.palette.energy_hot,
                'background': self.palette.bg_dark
            })
            
        elif self._current_mode == "alert":
            colors.update({
                'primary': self.palette.alert_bright,
                'secondary': self.palette.alert_base,
                'accent': self.palette.warning,
                'glow': self.palette.alert_bright,
                'background': self.palette.bg_dark
            })
            
        elif self._current_mode == "active":
            colors.update({
                'primary': self.palette.energy_hot,
                'secondary': self.palette.energy_base,
                'accent': self.palette.info_bright,
                'glow': self.palette.energy_bright,
                'background': self.palette.bg_dark
            })
            
        return colors
    
    def get_color(self, color_type: str, alpha: float = 1.0) -> Tuple[float, float, float, float]:
        """
        Get a color with smooth transitions and optional alpha.
        
        Args:
            color_type: Type of color ('primary', 'secondary', 'accent', 'glow', 'background')
            alpha: Alpha transparency (0.0 to 1.0)
        
        Returns:
            RGBA color tuple
        """
        current_colors = self._get_current_colors()
        target_color = current_colors.get(color_type, self.palette.info_base)
        
        # Apply transition if in progress
        progress = self._get_transition_progress()
        if progress < 1.0 and color_type in self._previous_colors:
            previous_color = self._previous_colors[color_type]
            final_color = self._interpolate_color(previous_color, target_color, progress)
        else:
            final_color = target_color
        
        return (*final_color, alpha)
    
    def get_dynamic_color(self, base_color_type: str, intensity: float = 1.0, 
                         time_offset: float = 0.0, alpha: float = 1.0) -> Tuple[float, float, float, float]:
        """
        Get a dynamically animated color with intensity and time-based variations.
        
        Args:
            base_color_type: Base color type to modify
            intensity: Intensity multiplier (0.0 to 2.0+)
            time_offset: Time offset for animation phase
            alpha: Alpha transparency
        
        Returns:
            RGBA color tuple with dynamic effects
        """
        base_color = self.get_color(base_color_type, 1.0)
        r, g, b, _ = base_color
        
        # Add time-based pulsing
        current_time = time.time() + time_offset
        pulse = 0.5 + 0.5 * math.sin(current_time * self.holographic_settings['pulse_speed'])
        
        # Apply intensity and pulse
        intensity_factor = intensity * (0.7 + 0.3 * pulse)
        
        final_r = min(1.0, r * intensity_factor)
        final_g = min(1.0, g * intensity_factor)
        final_b = min(1.0, b * intensity_factor)
        
        return (final_r, final_g, final_b, alpha)
    
    def get_holographic_effects(self) -> Dict[str, float]:
        """Get current holographic effect parameters."""
        base_settings = self.holographic_settings.copy()
        
        # Modify based on current mode
        if self._current_mode == "processing":
            base_settings['scan_speed'] *= 2.0
            base_settings['glow_intensity'] *= 1.3
            base_settings['pulse_speed'] *= 1.5
            
        elif self._current_mode == "alert":
            base_settings['glow_intensity'] *= 1.5
            base_settings['pulse_speed'] *= 3.0
            base_settings['scan_speed'] *= 3.0
            
        elif self._current_mode == "listening":
            base_settings['glow_alpha'] *= 1.2
            base_settings['fresnel_strength'] *= 1.1
            
        return base_settings
    
    def get_typography_style(self, text_type: str = "primary") -> Dict[str, Any]:
        """
        Get typography styling based on text type.
        
        Args:
            text_type: One of 'primary', 'secondary', 'accent', 'mono', 'title'
        
        Returns:
            Dictionary with font styling parameters
        """
        base_style = {
            'family': self.typography['primary_family'],
            'fallback': self.typography['fallback_family'],
            'weight': self.typography['weight_medium'],
            'letter_spacing': self.typography['letter_spacing']
        }
        
        if text_type == "title":
            base_style.update({
                'family': self.typography['primary_family'],
                'size': self.typography['size_large'],
                'weight': self.typography['weight_bold'],
                'color': self.get_color('primary', 0.9)
            })
            
        elif text_type == "secondary":
            base_style.update({
                'family': self.typography['secondary_family'],
                'size': self.typography['size_medium'],
                'weight': self.typography['weight_light'],
                'color': self.get_color('secondary', 0.7)
            })
            
        elif text_type == "mono":
            base_style.update({
                'family': self.typography['mono_family'],
                'size': self.typography['size_small'],
                'weight': self.typography['weight_light'],
                'color': self.get_color('accent', 0.6)
            })
            
        elif text_type == "accent":
            base_style.update({
                'family': self.typography['secondary_family'],
                'size': self.typography['size_medium'],
                'weight': self.typography['weight_medium'],
                'color': self.get_color('accent', 0.8)
            })
            
        else:  # primary
            base_style.update({
                'size': self.typography['size_medium'],
                'weight': self.typography['weight_medium'],
                'color': self.get_color('primary', 0.85)
            })
        
        return base_style
    
    def get_background_gradient(self, width: int, height: int) -> Dict[str, Any]:
        """
        Generate parameters for a dynamic background gradient.
        
        Args:
            width: Background width
            height: Background height
        
        Returns:
            Gradient parameters dictionary
        """
        current_time = time.time()
        
        # Base colors based on mode
        if self._current_mode == "processing":
            color1 = (*self.palette.bg_dark, 1.0)
            color2 = (0.08, 0.04, 0.02, 1.0)  # Warm dark
            color3 = (0.06, 0.08, 0.02, 1.0)  # Cool dark
        elif self._current_mode == "alert":
            color1 = (*self.palette.bg_dark, 1.0)
            color2 = (0.08, 0.02, 0.02, 1.0)  # Red-tinted dark
            color3 = (0.06, 0.04, 0.02, 1.0)  # Orange-tinted dark
        else:
            color1 = (*self.palette.bg_dark, 1.0)
            color2 = (0.04, 0.06, 0.10, 1.0)  # Blue-tinted dark
            color3 = (0.02, 0.05, 0.08, 1.0)  # Deep blue-tinted dark
        
        # Dynamic center glow
        glow_intensity = 0.05 + 0.03 * math.sin(current_time * 0.5)
        if self._current_mode == "processing":
            glow_intensity *= 1.5
        
        return {
            'type': 'radial',
            'center': (width // 2, height // 2),
            'colors': [color1, color2, color3],
            'glow_intensity': glow_intensity,
            'glow_radius': min(width, height) * 0.6
        }
    
    def apply_scan_lines(self, enable: bool = True) -> Dict[str, Any]:
        """Generate scan line effect parameters."""
        if not enable:
            return {'enabled': False}
        
        current_time = time.time()
        
        return {
            'enabled': True,
            'opacity': 0.08,
            'spacing': 3,
            'speed': 0.5,
            'offset': (current_time * 20) % 100,
            'color': self.get_color('accent', 0.1)
        }

# Global instance
color_scheme = JARVISColorScheme()
