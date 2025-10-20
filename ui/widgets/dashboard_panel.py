# widgets/dashboard_panel.py
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QFrame
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect
from PyQt5.QtGui import QFont
from ui.styles.style import apply_shadow_effect, Colors
from functools import partial

textsize = "7pt"
labelsize = "9pt"
titlesize = "11pt"
class DashboardPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("dashboardPanel")
        self.setup_ui()

    def setup_ui(self):
        self.labels = {
            "total_sessions": QLabel("Séances : --"),
            "total_profs": QLabel("Enseignants : --"),
            "violations": QLabel("Infractions : --"),
            "fitness": QLabel("Score Fitness : --")
     }
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # --- NAV BAR (buttons at the top) ---
        nav_bar = QHBoxLayout()
        nav_bar.setSpacing(8)
        self.buttons = {}

        for name in ["Résumé", "Infractions", "Graphes"]:
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setObjectName("navButton")
            btn.clicked.connect(partial(self.switch_page, name))
            self.buttons[name] = btn
            nav_bar.addWidget(btn)

        layout.addLayout(nav_bar)

        # --- BODY AREA ---
        self.stack = QStackedWidget()
        self.stack.setObjectName("dashboardStack")

        # --- PAGE: Résumé ---
        summary_page = QWidget()
        summary_layout = QVBoxLayout(summary_page)
        summary_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        summary_layout.setSpacing(10)

        self.labels = {
            "total_sessions": QLabel("Sessions totales : --"),
            "total_profs": QLabel("Professeurs totaux : --"),
            "violations": QLabel("Infractions : --"),
            "fitness": QLabel("Score de fitness : --")
        }

        for lbl in self.labels.values():
            lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
            lbl.setStyleSheet("font-size: 11pt;")
            summary_layout.addWidget(lbl)

        # --- PAGE: Violations ---
        violations_page = QLabel("⚠️ Journal des infractions sera affiché ici.")
        violations_page.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- PAGE: Charts ---
        chart_container = QFrame()
        chart_layout = QVBoxLayout(chart_container)
        chart_placeholder = QLabel("📈 Graphes et diagrammes seront affichés ici.")
        chart_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chart_layout.addWidget(chart_placeholder)

        # Add pages to stack
        self.stack.addWidget(summary_page)
        self.stack.addWidget(violations_page)
        self.stack.addWidget(chart_container)

        layout.addWidget(self.stack)
        layout.addStretch()

        # Shadow
        apply_shadow_effect(self, blur=20, offset=(0, -3), color=Colors.SHADOW_LIGHT)

        # Default active page
        self.switch_page("resumé")

    def switch_page(self, name):
        """Switch visible content and animate the transition."""
        index_map = {"Résumé": 0, "Infractions": 1, "Graphes": 2}
        new_index = index_map.get(name)
        if new_index is None:
            return  # Avoid crash if button name mismatched

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

    def update_stats(self, stats):
        """Update dashboard summary values."""
        if not hasattr(self, "labels"):
            return
        for key, lbl in self.labels.items():
            lbl.setText(f"{key.replace('_', ' ').title()} : {stats.get(key, '--')}")
