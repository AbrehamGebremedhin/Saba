"""
SABA UI Package - Enhanced JARVIS-style Interface

This package contains the complete user interface system for SABA,
featuring sophisticated color schemes, advanced visual effects,
holographic elements, and modern typography.
"""

# Core UI components
from .main import main
from .saba_window import SabaWindow
from .saba_gl import SabaGL
from .models import SphereModel

# Enhanced visual system
from .color_scheme import color_scheme, JARVISColorScheme, ColorPalette
from .visual_effects import (
    geometric_patterns, 
    holographic_effects, 
    data_displays, 
    particle_system,
    GeometricPatterns,
    HolographicEffects,
    DynamicDataDisplays,
    ParticleTrails
)
from .typography import typography, text_animations, TypographyManager, TextAnimations

# Audio analysis
from .audio_analyzer import AudioAnalyzer

__all__ = [
    # Main components
    'main', 'SabaWindow', 'SabaGL', 'SphereModel', 'AudioAnalyzer',
    
    # Color and visual systems
    'color_scheme', 'JARVISColorScheme', 'ColorPalette',
    'geometric_patterns', 'holographic_effects', 'data_displays', 'particle_system',
    'GeometricPatterns', 'HolographicEffects', 'DynamicDataDisplays', 'ParticleTrails',
    
    # Typography
    'typography', 'text_animations', 'TypographyManager', 'TextAnimations'
]