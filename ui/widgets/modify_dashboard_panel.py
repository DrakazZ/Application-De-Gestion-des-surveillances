# widgets/dashboard_panel_simple.py
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect
from ui.styles.style import apply_shadow_effect, Colors

class SimpleDashboardPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("dashboardPanel")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # --- NAV BAR (buttons at the top) ---
        nav_bar = QHBoxLayout()
        nav_bar.setSpacing(8)
        self.buttons = {}

        for name in ["Résumé", "Infractions"]:
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setObjectName("navButton")
            btn.clicked.connect(lambda _, n=name: self.switch_page(n))
            self.buttons[name] = btn
            nav_bar.addWidget(btn)

        layout.addLayout(nav_bar)

        # --- BODY AREA ---
        self.stack = QStackedWidget()
        self.stack.setObjectName("dashboardStack")

        # --- PAGE: Résumé ---
        summary_page = QLabel("📋 Résumé des données sera affiché ici.")
        summary_page.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- PAGE: Violations ---
        violations_page = QLabel("⚠️ Journal des infractions sera affiché ici.")
        violations_page.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Add pages to stack
        self.stack.addWidget(summary_page)
        self.stack.addWidget(violations_page)

        layout.addWidget(self.stack)
        layout.addStretch()

        # Shadow
        apply_shadow_effect(self, blur=20, offset=(0, -3), color=Colors.SHADOW_LIGHT)

        # Default active page
        self.switch_page("Résumé")

    def switch_page(self, name):
        """Switch visible content and animate the transition."""
        index_map = {"Résumé": 0, "Infractions": 1}
        new_index = index_map[name]

        # Update button styles
        for n, b in self.buttons.items():
            b.setChecked(n == name)

        # Simple animation (slide)
        current_widget = self.stack.currentWidget()
        new_widget = self.stack.widget(new_index)

        if current_widget != new_widget:
            animation = QPropertyAnimation(new_widget, b"geometry")
            new_widget.show()
            start_rect = QRect(self.stack.width(), 0, self.stack.width(), self.stack.height())
            end_rect = QRect(0, 0, self.stack.width(), self.stack.height())
            new_widget.setGeometry(start_rect)
            animation.setDuration(400)
            animation.setStartValue(start_rect)
            animation.setEndValue(end_rect)
            animation.start()

        self.stack.setCurrentIndex(new_index)

        # Shadow
        apply_shadow_effect(self, blur=20, offset=(0, -3), color=Colors.SHADOW_LIGHT)
