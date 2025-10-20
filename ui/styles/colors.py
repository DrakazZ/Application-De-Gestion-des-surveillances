"""
Color System - OKLCH to RGB Conversion
Provides consistent, perceptually uniform colors
"""

from colorsys import hls_to_rgb
import math


def oklch_to_rgb(l, c, h):
    """
    Convert OKLCH to RGB (approximation via HLS)
    
    OKLCH:
    - L: lightness (0-1)
    - C: chroma (0-0.4)
    - H: hue (0-360)
    
    Returns: (r, g, b) tuple (0-255)
    """
    # Convert OKLCH hue to HLS hue (normalize to 0-1)
    hls_h = h / 360.0
    
    # Map lightness (OKLCH L is perceptually linear)
    hls_l = l
    
    # Map chroma to saturation (approximation)
    hls_s = min(1.0, c * 2.5)  # Scale chroma to saturation
    
    # Convert HLS to RGB
    r, g, b = hls_to_rgb(hls_h, hls_l, hls_s)
    
    return int(r * 255), int(g * 255), int(b * 255)


def rgb_to_hex(r, g, b):
    """Convert RGB to hex color string"""
    return f"#{r:02x}{g:02x}{b:02x}"


def oklch_to_hex(l, c, h):
    """Direct OKLCH to hex conversion"""
    r, g, b = oklch_to_rgb(l, c, h)
    return rgb_to_hex(r, g, b)


# ==================== COLOR PALETTE ====================

class Colors:
    """Application color palette"""

    # Backgrounds
    BG_DARK = oklch_to_hex(0.92, 0.035, 240)     # Slightly darker base
    BG = oklch_to_hex(0.96, 0.035, 240)          # Main background
    BG_LIGHT = oklch_to_hex(1, 0.035, 240)     # Elevated panels

    # Text
    TEXT = oklch_to_hex(0.15, 0.07, 240)         # Primary text
    TEXT_MUTED = oklch_to_hex(0.4, 0.07, 240)    # Secondary text

    # UI Elements
    HIGHLIGHT = oklch_to_hex(1.0, 0.07, 240)     # Hover highlights
    BORDER = oklch_to_hex(0.6, 0.07, 240)        # Primary borders
    BORDER_MUTED = oklch_to_hex(0.7, 0.07, 240)  # Subtle borders

    # Action Colors
    PRIMARY = oklch_to_hex(0.4, 0.13, 243)        # Main actions (purple)
    SECONDARY = oklch_to_hex(0.4, 0.07, 235)       # Secondary actions (yellow-green)
    
    # Status Colors
    DANGER = oklch_to_hex(0.5, 0.05, 30)         # Errors (red)
    WARNING = oklch_to_hex(0.5, 0.05, 100)       # Warnings (yellow)
    SUCCESS = oklch_to_hex(0.5, 0.05, 160)       # Success (green)
    INFO = oklch_to_hex(0.5, 0.05, 260)          # Info (blue)
    
    # Shadows (with alpha)
    SHADOW_LIGHT = "rgba(0, 0, 0, 0.05)"
    SHADOW_MEDIUM = "rgba(0, 0, 0, 0.10)"
    SHADOW_HEAVY = "rgba(0, 0, 0, 0.20)"


# ==================== HELPER FUNCTIONS ====================

def get_hover_color(base_hex, lighten=0.05):
    """Generate hover color (slightly lighter)"""
    # Simple lighten by adding to RGB values
    r = int(base_hex[1:3], 16)
    g = int(base_hex[3:5], 16)
    b = int(base_hex[5:7], 16)
    
    r = min(255, int(r + (255 - r) * lighten))
    g = min(255, int(g + (255 - g) * lighten))
    b = min(255, int(b + (255 - b) * lighten))
    
    return rgb_to_hex(r, g, b)


def get_pressed_color(base_hex, darken=0.10):
    """Generate pressed color (slightly darker)"""
    r = int(base_hex[1:3], 16)
    g = int(base_hex[3:5], 16)
    b = int(base_hex[5:7], 16)
    
    r = int(r * (1 - darken))
    g = int(g * (1 - darken))
    b = int(b * (1 - darken))
    
    return rgb_to_hex(r, g, b)


# ==================== EXPORT FOR QSS ====================

def generate_qss_variables():
    """Generate CSS variable definitions for Qt stylesheets"""
    return f"""
/* Color Variables */
* {{
    qproperty-bg-dark: {Colors.BG_DARK};
    qproperty-bg: {Colors.BG};
    qproperty-bg-light: {Colors.BG_LIGHT};
    qproperty-text: {Colors.TEXT};
    qproperty-text-muted: {Colors.TEXT_MUTED};
    qproperty-border: {Colors.BORDER};
    qproperty-primary: {Colors.PRIMARY};
    qproperty-secondary: {Colors.SECONDARY};
    qproperty-success: {Colors.SUCCESS};
    qproperty-warning: {Colors.WARNING};
    qproperty-danger: {Colors.DANGER};
    qproperty-info: {Colors.INFO};
}}
"""


if __name__ == "__main__":
    # Test color conversion
    print("Color Palette Preview:")
    print(f"BG_DARK: {Colors.BG_DARK}")
    print(f"BG: {Colors.BG}")
    print(f"BG_LIGHT: {Colors.BG_LIGHT}")
    print(f"TEXT: {Colors.TEXT}")
    print(f"PRIMARY: {Colors.PRIMARY}")
    print(f"SECONDARY: {Colors.SECONDARY}")
    print(f"SUCCESS: {Colors.SUCCESS}")
    print(f"WARNING: {Colors.WARNING}")
    print(f"DANGER: {Colors.DANGER}")