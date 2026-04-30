"""
Global Qt Stylesheet
Defines consistent visual language across the application
"""

from ui.styles.colors import Colors, get_hover_color, get_pressed_color


def get_global_stylesheet():
    """
    Generate complete application stylesheet
    Uses color system for consistency
    """
    
    return f"""
/* ==================== GLOBAL RESET ==================== */
* {{
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 10pt;
    color: {Colors.TEXT};
}}

QMainWindow, QWidget {{
    background-color: {Colors.BG_DARK};
}}


/* ==================== HEADER BAR ==================== */

QFrame#header {{
    background-color: {Colors.BG};
    border-bottom: 1px solid {Colors.BORDER_MUTED};
}}

QLabel#logo {{
    color: {Colors.PRIMARY};
    font-size: 20pt;
    font-weight: bold;
    padding: 0 10px;
}}


/* ==================== NAVIGATION BUTTONS ==================== */

QPushButton#navButton {{
    background-color: transparent;
    border: none;
    border-bottom: 3px solid transparent;
    padding: 20px 24px;
    font-size: 11pt;
    font-weight: 500;
    color: {Colors.TEXT_MUTED};
}}

QPushButton#navButton:hover {{
    color: {Colors.TEXT};
    background-color: {get_hover_color(Colors.BG_LIGHT, 0.05)};
}}

QPushButton#navButton:checked {{
    color: {Colors.PRIMARY};
    border-bottom-color: {Colors.PRIMARY};
    font-weight: bold;
    background-color: transparent;
}}
/* ==================== TOOL PANELS ==================== */
QFrame#toolPanel {{
    background-color: {Colors.BG}; 
    border: 1px solid {Colors.BORDER_MUTED};
    border-radius: 10px;
    padding: 14px;
    min-height: 160px;
}}

QFrame#toolPanel:hover {{
    border-color: {Colors.PRIMARY};
    background-color: rgba(255, 255, 255, 0.02);
}}

QLabel#toolPanelTitle {{
    font-size: 11pt;
    font-weight: 600;
    color: {Colors.TEXT};
    padding-bottom: 6px;
    border-bottom: 1px solid {Colors.BORDER_MUTED};
    margin-bottom: 8px;
}}


/* ==================== PANELS (FRAMES/GROUPBOXES) ==================== */

/* Column frames (transparent containers) */
QFrame#columnFrame {{
    background-color: transparent;
    border: none;
}}

/* Base Panel */
QFrame#basePanel, QGroupBox#basePanel {{
    background-color: {Colors.BG};
    border: 1px solid {Colors.BORDER_MUTED};
    border-radius: 12px;
    padding: 16px;
}}

/* Elevated Panel */
QFrame#elevatedPanel, QGroupBox#elevatedPanel {{
    background-color: {Colors.BG};
    border: 1px solid {Colors.BORDER_MUTED};
    border-radius: 12px;
    padding: 16px;
}}


/* ==================== BUTTONS ==================== */

/* Primary Button */
QPushButton#primaryButton {{
    background-color: {Colors.PRIMARY};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 24px;
    font-weight: bold;
    min-height: 20px;
}}

QPushButton#primaryButton:hover {{
    background-color: {get_hover_color(Colors.PRIMARY, 0.15)};
}}

QPushButton#primaryButton:pressed {{
    background-color: {get_pressed_color(Colors.PRIMARY, 0.15)};
}}

QPushButton#primaryButton:disabled {{
    background-color: {Colors.BORDER_MUTED};
    color: {Colors.TEXT_MUTED};
}}

/* Secondary Button */
QPushButton#secondaryButton {{
    background-color: {Colors.SECONDARY};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-weight: 500;
    min-height: 20px;
}}

QPushButton#secondaryButton:hover {{
    background-color: {get_hover_color(Colors.SECONDARY, 0.15)};
}}

QPushButton#secondaryButton:pressed {{
    background-color: {get_pressed_color(Colors.SECONDARY, 0.15)};
}}

/* Success Button */
QPushButton#successButton {{
    background-color: {Colors.SECONDARY};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 24px;
    font-weight: bold;
    min-height: 20px;
}}

QPushButton#successButton:hover {{
    background-color: {get_hover_color(Colors.SECONDARY, 0.15)};
}}

QPushButton#successButton:pressed {{
    background-color: {get_pressed_color(Colors.SECONDARY, 0.15)};
}}


/* ==================== INPUT FIELDS ==================== */

QLineEdit, QTextEdit, QSpinBox {{
    background-color: white;
    border: 1px solid {Colors.BORDER_MUTED};
    border-radius: 6px;
    padding: 8px 12px;
    min-height: 32px;
    selection-background-color: {Colors.PRIMARY};
}}

QLineEdit:focus, QTextEdit:focus, QSpinBox:focus {{
    border-color: {Colors.PRIMARY};
}}

QLineEdit:disabled, QTextEdit:disabled, QSpinBox:disabled {{
    background-color: {Colors.BG_DARK};
    color: {Colors.TEXT_MUTED};
}}

QLineEdit::placeholder {{
    color: {Colors.TEXT_MUTED};
}}


/* ==================== COMBOBOX (Dropdowns) ==================== */

QComboBox {{
    background-color: white;
    border: 1px solid {Colors.BORDER_MUTED};
    border-radius: 6px;
    padding: 3px 6px;
    min-height: 16px;
    min-width: 30px;
}}

QComboBox:hover {{
    border-color: {Colors.PRIMARY};
}}

QComboBox::drop-down {{
    border: none;
    width: 30px;
}}

QComboBox QAbstractItemView {{
    background-color: white;
    border: 1px solid {Colors.BORDER};
    selection-background-color: {Colors.PRIMARY};
    selection-color: white;
    padding: 4px;
}}


/* ==================== LABELS ==================== */

QLabel {{
    color: {Colors.TEXT};
    background-color: transparent;
    margin-top: 4px;
    margin-bottom: 2px;
}}

QLabel#sectionLabel {{
    font-size: 12pt;
    font-weight: 600;
    color: {Colors.TEXT};
    padding-bottom: 8px;
}}

QLabel#mutedLabel {{
    color: {Colors.TEXT_MUTED};
    font-size: 9pt;
}}


/* ==================== DASHBOARD PANEL ==================== */

QWidget#dashboardPanel {{
    background-color: transparent;
    border: none;
}}

QLabel#dashboardTitle {{
    font-size: 13pt;
    font-weight: 600;
    color: {Colors.TEXT};
    padding-bottom: 8px;
}}

QLabel#dashboardPlaceholder {{
    color: {Colors.TEXT_MUTED};
    font-size: 10pt;
    padding: 12px;
}}

/* Chart frames inside dashboard */
QFrame#chartFrame0, QFrame#chartFrame1, QFrame#chartFrame2 {{
    background-color: {Colors.BG};
    border: 1px solid {Colors.BORDER_MUTED};
    border-radius: 10px;
    min-height: 150px;
}}

QFrame#chartFrame0:hover, QFrame#chartFrame1:hover, QFrame#chartFrame2:hover {{
    border-color: {Colors.PRIMARY};
    background-color: {get_hover_color(Colors.BG_LIGHT, 0.08)};
}}


/* ==================== SCROLLBAR ==================== */

QScrollBar:vertical {{
    border: none;
    background-color: {Colors.BG_DARK};
    width: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:vertical {{
    background-color: {Colors.BORDER};
    border-radius: 6px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {Colors.PRIMARY};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}


/* ==================== TOOLTIPS ==================== */

QToolTip {{
    background-color: {Colors.TEXT};
    color: white;
    border: 1px solid {Colors.BORDER};
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 9pt;
}}

"""


def apply_shadow_effect(widget, blur=10, offset=(2, 2), color=Colors.SHADOW_MEDIUM):
    """
    Apply drop shadow to widget for depth
    
    Args:
        widget: QWidget to apply shadow to
        blur: Shadow blur radius
        offset: (x, y) offset tuple
        color: Shadow color (rgba string)
    """
    from PyQt5.QtWidgets import QGraphicsDropShadowEffect
    from PyQt5.QtGui import QColor
    from PyQt5.QtCore import QPoint
    
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setOffset(QPoint(*offset))
    
    # Parse rgba color
    if color.startswith("rgba"):
        import re
        match = re.search(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)', color)
        if match:
            r, g, b, a = match.groups()
            shadow.setColor(QColor(int(r), int(g), int(b), int(float(a) * 255)))
    
    widget.setGraphicsEffect(shadow)