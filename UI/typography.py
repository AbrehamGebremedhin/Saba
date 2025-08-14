"""
Advanced Typography System for JARVIS-style Interface
Implements modern, geometric fonts with proper hierarchy and spacing.
"""

from typing import Dict, Any, Optional, Tuple
from PyQt5.QtGui import QFont, QFontDatabase, QColor
from PyQt5.QtCore import Qt
from .color_scheme import color_scheme

class TypographyManager:
    """Manages font loading, styling, and text rendering for the JARVIS interface."""
    
    def __init__(self):
        self.font_database = None
        self.loaded_fonts = {}
        self.fallback_fonts = {
            'primary': ['Orbitron', 'Rajdhani', 'Segoe UI', 'Arial'],
            'secondary': ['Rajdhani', 'Exo 2', 'Segoe UI', 'Arial'],
            'monospace': ['Consolas', 'Courier New', 'monospace'],
            'display': ['Orbitron', 'Impact', 'Arial Black']
        }
        
        # Initialize fonts when needed (after QApplication is created)
    
    def _ensure_initialized(self):
        """Ensure font system is initialized after QApplication creation."""
        if self.font_database is None:
            try:
                self.font_database = QFontDatabase()
                self._initialize_fonts()
            except:
                # Fallback initialization if QApplication not ready
                self.font_database = None
                self._set_fallback_fonts()
    
    def _set_fallback_fonts(self):
        """Set fallback fonts when QFontDatabase is not available."""
        self.loaded_fonts = {
            'primary': 'Arial',
            'secondary': 'Arial',
            'monospace': 'Courier New',
            'display': 'Arial'
        }
        
    def _initialize_fonts(self):
        """Initialize font system and attempt to load preferred fonts."""
        if self.font_database is None:
            self._set_fallback_fonts()
            return
            
        # Get all available system fonts
        available_families = self.font_database.families()
        
        # Check which preferred fonts are available
        for category, font_list in self.fallback_fonts.items():
            for font_name in font_list:
                if font_name in available_families:
                    self.loaded_fonts[category] = font_name
                    break
            
            # If no preferred font found, use system default
            if category not in self.loaded_fonts:
                if category == 'monospace':
                    self.loaded_fonts[category] = 'Courier New'
                else:
                    self.loaded_fonts[category] = 'Arial'
    
    def get_font(self, style_type: str = 'primary', 
                 size: int = 12, 
                 weight: int = QFont.Normal,
                 italic: bool = False) -> QFont:
        """
        Get a configured QFont object.
        
        Args:
            style_type: Font category ('primary', 'secondary', 'monospace', 'display')
            size: Font size in points
            weight: Font weight (QFont.Light, QFont.Normal, QFont.Bold)
            italic: Whether font should be italic
        
        Returns:
            Configured QFont object
        """
        self._ensure_initialized()
        family = self.loaded_fonts.get(style_type, 'Arial')
        font = QFont(family, size, weight, italic)
        
        # Enable font hinting for better rendering
        font.setHintingPreference(QFont.PreferDefaultHinting)
        font.setStyleStrategy(QFont.PreferAntialias)
        
        return font
    
    def get_title_font(self, size: int = 24) -> QFont:
        """Get font for main titles and headers."""
        return self.get_font('display', size, QFont.Bold)
    
    def get_subtitle_font(self, size: int = 16) -> QFont:
        """Get font for subtitles and secondary headers."""
        return self.get_font('primary', size, QFont.DemiBold)
    
    def get_body_font(self, size: int = 12) -> QFont:
        """Get font for body text."""
        return self.get_font('secondary', size, QFont.Normal)
    
    def get_caption_font(self, size: int = 10) -> QFont:
        """Get font for captions and small text."""
        return self.get_font('secondary', size, QFont.Light)
    
    def get_mono_font(self, size: int = 11) -> QFont:
        """Get monospace font for code and data."""
        return self.get_font('monospace', size, QFont.Normal)
    
    def get_status_font(self, size: int = 10) -> QFont:
        """Get font for status indicators."""
        font = self.get_font('secondary', size, QFont.Medium)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 2.0)  # Increased letter spacing
        font.setCapitalization(QFont.AllUppercase)
        return font
    
    def create_text_style(self, text_type: str = 'body') -> Dict[str, Any]:
        """
        Create a comprehensive text style configuration.
        
        Args:
            text_type: Type of text ('title', 'subtitle', 'body', 'caption', 'status', 'data')
        
        Returns:
            Dictionary containing font and color information
        """
        if text_type == 'title':
            return {
                'font': self.get_title_font(28),
                'color': self._get_text_color('primary', 0.95),
                'shadow': True,
                'shadow_color': self._get_text_color('glow', 0.3),
                'letter_spacing': 3.0,
                'line_height': 1.2
            }
        
        elif text_type == 'subtitle':
            return {
                'font': self.get_subtitle_font(18),
                'color': self._get_text_color('secondary', 0.85),
                'shadow': False,
                'letter_spacing': 2.0,
                'line_height': 1.3
            }
        
        elif text_type == 'body':
            return {
                'font': self.get_body_font(14),
                'color': self._get_text_color('primary', 0.8),
                'shadow': False,
                'letter_spacing': 0.5,
                'line_height': 1.4
            }
        
        elif text_type == 'caption':
            return {
                'font': self.get_caption_font(11),
                'color': self._get_text_color('secondary', 0.6),
                'shadow': False,
                'letter_spacing': 1.0,
                'line_height': 1.3
            }
        
        elif text_type == 'status':
            return {
                'font': self.get_status_font(10),
                'color': self._get_text_color('accent', 0.9),
                'shadow': True,
                'shadow_color': self._get_text_color('glow', 0.2),
                'letter_spacing': 2.5,
                'line_height': 1.0
            }
        
        elif text_type == 'data':
            return {
                'font': self.get_mono_font(12),
                'color': self._get_text_color('accent', 0.85),
                'shadow': False,
                'letter_spacing': 0.8,
                'line_height': 1.2
            }
        
        else:  # Default to body
            return self.create_text_style('body')
    
    def _get_text_color(self, color_type: str, alpha: float) -> QColor:
        """Convert color scheme colors to QColor objects."""
        r, g, b, a = color_scheme.get_color(color_type, alpha)
        return QColor(int(r * 255), int(g * 255), int(b * 255), int(a * 255))
    
    def apply_text_effects(self, painter, style: Dict[str, Any], text: str, 
                          rect, alignment: int = Qt.AlignLeft):
        """
        Apply text effects and render text with the given style.
        
        Args:
            painter: QPainter object
            style: Text style dictionary
            text: Text to render
            rect: QRect for text bounds
            alignment: Qt alignment flags
        """
        painter.setFont(style['font'])
        
        # Draw shadow if enabled
        if style.get('shadow', False) and 'shadow_color' in style:
            shadow_rect = rect.adjusted(1, 1, 1, 1)
            painter.setPen(style['shadow_color'])
            painter.drawText(shadow_rect, alignment, text)
        
        # Draw main text
        painter.setPen(style['color'])
        painter.drawText(rect, alignment, text)
    
    def get_text_metrics(self, text: str, style_type: str = 'body') -> Dict[str, int]:
        """
        Get text metrics for layout calculations.
        
        Args:
            text: Text to measure
            style_type: Style type to use for measurement
        
        Returns:
            Dictionary with width, height, and other metrics
        """
        style = self.create_text_style(style_type)
        font = style['font']
        
        from PyQt5.QtGui import QFontMetrics
        metrics = QFontMetrics(font)
        
        return {
            'width': metrics.horizontalAdvance(text),
            'height': metrics.height(),
            'ascent': metrics.ascent(),
            'descent': metrics.descent(),
            'leading': metrics.leading(),
            'line_spacing': int(metrics.height() * style.get('line_height', 1.4))
        }

class TextAnimations:
    """Text animation effects for dynamic text displays."""
    
    @staticmethod
    def typing_effect(text: str, progress: float) -> str:
        """Simulate typing effect by revealing characters progressively."""
        if progress <= 0:
            return ""
        if progress >= 1:
            return text
        
        visible_chars = int(len(text) * progress)
        return text[:visible_chars]
    
    @staticmethod
    def scan_effect(text: str, progress: float, scan_char: str = '█') -> str:
        """Simulate scanning effect with a block character."""
        if progress <= 0:
            return scan_char * len(text)
        if progress >= 1:
            return text
        
        visible_chars = int(len(text) * progress)
        result = text[:visible_chars]
        
        # Add scanning block for remaining characters
        remaining = len(text) - visible_chars
        if remaining > 0:
            result += scan_char * min(3, remaining)
        
        return result
    
    @staticmethod
    def glitch_effect(text: str, intensity: float = 0.1) -> str:
        """Add glitch effect by randomly replacing some characters."""
        if intensity <= 0:
            return text
        
        import random
        glitch_chars = '█▓▒░▄▀▐▌'
        result = list(text)
        
        for i in range(len(result)):
            if random.random() < intensity:
                result[i] = random.choice(glitch_chars)
        
        return ''.join(result)
    
    @staticmethod
    def decode_effect(text: str, progress: float) -> str:
        """Simulate decoding effect where characters resolve over time."""
        if progress >= 1:
            return text
        
        import random
        decode_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*'
        result = []
        
        for i, char in enumerate(text):
            char_progress = max(0, progress * 2 - (i / len(text)))
            if char_progress >= 1:
                result.append(char)
            elif char_progress > 0:
                if random.random() < char_progress:
                    result.append(char)
                else:
                    result.append(random.choice(decode_chars))
            else:
                result.append(random.choice(decode_chars))
        
        return ''.join(result)

# Global typography manager instance
typography = TypographyManager()
text_animations = TextAnimations()
