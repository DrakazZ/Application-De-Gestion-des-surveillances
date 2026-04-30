from PyQt5.QtWidgets import (
    QFrame, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QLineEdit, QFileDialog, QMessageBox , QDialog
)

from PyQt5.QtCore import Qt,pyqtSignal
from ui.styles.style import apply_shadow_effect
from ui.widgets.ga_config_dialog import GAConfigDialog

textsize = "7pt"
labelsize = "9pt"
titlesize = "11pt"
class DataInputPanel(QFrame):
    """Compact data input panel for selecting required Excel files."""
    
    import_requested = pyqtSignal(dict) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.files = {
            "calendrier": "",
            "professeurs": "",
            "souhaits": "",
            "salles": ""
        }
        self.ga_settings = {'population': 70, 'generations': 300}
        self.setup_ui()

    def setup_ui(self):
        self.setObjectName("basePanel")
        apply_shadow_effect(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        title = QLabel("📂 Importation des fichiers")
        title.setObjectName("sectionLabel")
        title.setStyleSheet(f"font-size: {titlesize}; font-weight: bold;")
        layout.addWidget(title)

        # === File rows ===
        layout.addLayout(self._create_pdf_row("Calendrier", "calendrier"))
        layout.addLayout(self._create_file_row("Professeurs", "professeurs"))
        layout.addLayout(self._create_file_row("Souhaits", "souhaits"))
        layout.addLayout(self._create_file_row("Répartition des salles", "salles"))

        layout.addStretch()

        # === Import button ===
        self.import_btn = QPushButton("Importe")
        self.import_btn.setObjectName("primaryButton")
        self.import_btn.setFixedHeight(12)
        self.import_btn.setStyleSheet(f"font-size: {textsize};")
        layout.addWidget(self.import_btn, alignment=Qt.AlignCenter)

        # === GA Config button ===
        self.ga_config_btn = QPushButton("paramètres GA")
        self.ga_config_btn.setObjectName("secondaryButton")
        self.ga_config_btn.setFixedHeight(12)
        self.ga_config_btn.setStyleSheet(f"font-size: {textsize};")
        layout.addWidget(self.ga_config_btn, alignment=Qt.AlignCenter)


        # Connections
        self.import_btn.clicked.connect(self.import_files)
        self.ga_config_btn.clicked.connect(self.open_ga_config)

    # -----------------------------
    # Helper: build one compact row
    # -----------------------------
    def _create_pdf_row(self, label_text, key):
        # Create a small vertical container for each field section
        row_layout = QVBoxLayout()
        row_layout.setSpacing(4)
        row_layout.setContentsMargins(0, 6, 0, 6)  # Add breathing room

        # Label on its own row
        label = QLabel(label_text)
        label.setObjectName("fieldLabel")
        label.setStyleSheet(f"""
            font-size: {labelsize};
            font-weight: 500;
            margin-bottom: 2px;
        """)

        # Horizontal row for input and button
        hbox = QHBoxLayout()
        hbox.setSpacing(6)

        line_edit = QLineEdit()
        line_edit.setPlaceholderText(f"Sélectionnez le fichier {label_text.lower()}")
        line_edit.setReadOnly(True)
        line_edit.setFixedHeight(20)  # slightly taller so text isn’t cramped
        line_edit.setStyleSheet(f"font-size: {textsize}; padding: 2px 4px;")

        browse_btn = QPushButton("Parcourir")
        browse_btn.setObjectName("secondaryButton")
        browse_btn.setFixedHeight(15)
        browse_btn.setFixedWidth(90)
        browse_btn.setStyleSheet(f"font-size: {textsize};")
        browse_btn.clicked.connect(lambda: self._browse_pdf(key, line_edit))

        # Add widgets
        hbox.addWidget(line_edit)
        hbox.addWidget(browse_btn)

        # Stack label above input+button
        row_layout.addWidget(label)
        row_layout.addLayout(hbox)

        # Store references
        setattr(self, f"{key}_edit", line_edit)
        setattr(self, f"{key}_btn", browse_btn)

        return row_layout
    
    def _create_file_row(self, label_text, key):
        # Create a small vertical container for each field section
        row_layout = QVBoxLayout()
        row_layout.setSpacing(4)
        row_layout.setContentsMargins(0, 6, 0, 6)  # Add breathing room

        # Label on its own row
        label = QLabel(label_text)
        label.setObjectName("fieldLabel")
        label.setStyleSheet(f"""
            font-size: {labelsize};
            font-weight: 500;
            margin-bottom: 2px;
        """)

        # Horizontal row for input and button
        hbox = QHBoxLayout()
        hbox.setSpacing(6)

        line_edit = QLineEdit()
        line_edit.setPlaceholderText(f"Sélectionnez le fichier {label_text.lower()}")
        line_edit.setReadOnly(True)
        line_edit.setFixedHeight(20)  # slightly taller so text isn’t cramped
        line_edit.setStyleSheet(f"font-size: {textsize}; padding: 2px 4px;")

        browse_btn = QPushButton("Parcourir")
        browse_btn.setObjectName("secondaryButton")
        browse_btn.setFixedHeight(15)
        browse_btn.setFixedWidth(90)
        browse_btn.setStyleSheet(f"font-size: {textsize};")
        browse_btn.clicked.connect(lambda: self._browse_file(key, line_edit))

        # Add widgets
        hbox.addWidget(line_edit)
        hbox.addWidget(browse_btn)

        # Stack label above input+button
        row_layout.addWidget(label)
        row_layout.addLayout(hbox)

        # Store references
        setattr(self, f"{key}_edit", line_edit)
        setattr(self, f"{key}_btn", browse_btn)

        return row_layout


    # -----------------------------
    # File browsing logic
    # -----------------------------
    def _browse_file(self, key, line_edit):
        path, _ = QFileDialog.getOpenFileName(
            self, f"Sélectionner le fichier {key}", "", "Excel Files (*.xlsx *.xls)"
        )
        if path:
            self.files[key] = path
            line_edit.setText(path)
            print(f"✅ {key.capitalize()} sélectionné : {path}")

    def _browse_pdf(self, key, line_edit):
        path, _ = QFileDialog.getOpenFileName(
            self, f"Sélectionner le fichier {key}", "", "PDF Files (*.pdf)"
        )
        if path:
            self.files[key] = path
            line_edit.setText(path)
            print(f"✅ {key.capitalize()} sélectionné : {path}")

    # -----------------------------
    # buttons logic
    # -----------------------------
    def import_files(self):
            self.import_requested.emit(self.files)

    def open_ga_config(self):
        dialog = GAConfigDialog(
            self, 
            population=self.ga_settings['population'], 
            generations=self.ga_settings['generations']
        )
        if dialog.exec_() == QDialog.Accepted:
            pop, gen = dialog.get_values()
            print(f"GA settings updated: population={pop}, generations={gen}")
            self.ga_settings['population'] = pop
            self.ga_settings['generations'] = gen

