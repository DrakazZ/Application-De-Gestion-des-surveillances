from PyQt5.QtWidgets import (
    QFrame, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox, QSpinBox
)
from PyQt5.QtCore import Qt
from ui.styles.style import apply_shadow_effect


textsize = "7pt"
labelsize = "9pt"
titlesize = "11pt"
class GradePanel(QFrame):
    """Handles rank limit configuration."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rank_limits = {}  # Dict to store {rank: limit}
        self.ranks = ["MA","V","PTC","PR","VA","AC","AS","EX","PES","MC"]
        self.setup_ui()

    def setup_ui(self):
        self.setObjectName("basePanel")
        apply_shadow_effect(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("🧮 Configuration des limites par grade")
        title.setObjectName("sectionLabel")
        layout.addWidget(title)

        # Dropdown + input
        input_layout = QHBoxLayout()

        self.rank_dropdown = QComboBox()
        self.rank_dropdown.addItems(self.ranks)
        input_layout.addWidget(QLabel("Sélectionner le grade :"))
        input_layout.addWidget(self.rank_dropdown)

        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(1, 100)  # adjust max as needed
        self.limit_spin.setValue(5)
        input_layout.addWidget(QLabel("Définir la limite :"))
        input_layout.addWidget(self.limit_spin)

        layout.addLayout(input_layout)

        # Save button
        self.save_btn = QPushButton("Enregistrer")
        self.save_btn.setObjectName("successButton")
        layout.addWidget(self.save_btn)
        layout.addStretch()

        # Connect button
        self.save_btn.clicked.connect(self.save_limit)

    def save_limit(self):
        rank = self.rank_dropdown.currentText()
        limit = self.limit_spin.value()
        self.rank_limits[rank] = limit
        print(f"💾 Saved: {rank} → {limit}")
        print("Current Rank Limits:", self.rank_limits)
