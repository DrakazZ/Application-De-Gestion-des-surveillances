# ui/widgets/export_panel.py
from PyQt5.QtWidgets import (
    QFrame, QLabel, QPushButton, QVBoxLayout, QLineEdit, 
    QFileDialog, QMessageBox, QCheckBox, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from ui.styles.style import apply_shadow_effect
from workers.db_handler import DBHandler
import pandas as pd


textsize = "7pt"
labelsize = "9pt"
titlesize = "11pt"


class ExportPanel(QFrame):
    """Handles export controls and output location selection."""
    
    export_requested = pyqtSignal(dict)  # Signal to trigger export with config

    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_result = None  # Store last scheduling result
        self.setup_ui()

    def setup_ui(self):
        self.setObjectName("basePanel")
        apply_shadow_effect(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("📤 Paramètres d'export")
        title.setObjectName("sectionLabel")
        layout.addWidget(title)

        # Export path selection
        self.path_field = QLineEdit()
        self.path_field.setPlaceholderText("Emplacement d'exportation...")
        layout.addWidget(self.path_field)

        self.browse_btn = QPushButton("Parcourir")
        self.browse_btn.setObjectName("secondaryButton")
        layout.addWidget(self.browse_btn)

        # Export options group
        options_group = QGroupBox("Options d'export")
        options_layout = QVBoxLayout()
        
        self.export_excel_cb = QCheckBox("Exporter Excel/CSV")
        self.export_excel_cb.setChecked(True)
        self.export_excel_cb.setToolTip("Exporter les résultats en fichiers Excel et CSV")
        
        self.export_word_cb = QCheckBox("Générer documents Word")
        self.export_word_cb.setChecked(True)
        self.export_word_cb.setToolTip("Générer convocations et affectations (DOCX)")
        
        self.export_stats_cb = QCheckBox("Exporter statistiques")
        self.export_stats_cb.setChecked(True)
        self.export_stats_cb.setToolTip("Exporter rapport statistique détaillé")
        
        options_layout.addWidget(self.export_excel_cb)
        options_layout.addWidget(self.export_word_cb)
        options_layout.addWidget(self.export_stats_cb)
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Export button
        self.export_btn = QPushButton("Exporter les résultats")
        self.export_btn.setObjectName("primaryButton")
        self.export_btn.setEnabled(False)  # Disabled until results available
        layout.addWidget(self.export_btn)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #666; font-size: 8pt;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Connect actions
        self.browse_btn.clicked.connect(self.browse_folder)
        self.export_btn.clicked.connect(self.export_files)

    def browse_folder(self):
        """Select export directory"""
        path = QFileDialog.getExistingDirectory(
            self, 
            "Sélectionner le dossier d'exportation"
        )
        if path:
            self.path_field.setText(path)

    def set_result(self, result):
        """
        Store scheduling result and enable export button.
        Called by main window after successful scheduling.
        
        Args:
            result: Dictionary from solve_hybrid containing scheduling results
        """
        self.last_result = result
        self.export_btn.setEnabled(True)
        self.status_label.setText("✓ Résultats prêts à exporter")

    def clear_result(self):
        """Clear stored result and disable export"""
        self.last_result = None
        self.export_btn.setEnabled(False)
        self.status_label.setText("")

    def export_files(self):
        """Execute export with selected options"""
        export_path = self.path_field.text().strip()
        
        # Validate
        if not export_path:
            QMessageBox.warning(
                self, 
                "Attention", 
                "⚠️ Veuillez choisir un dossier d'exportation."
            )
            return
        
        if not self.last_result:
            QMessageBox.warning(
                self, 
                "Attention", 
                "⚠️ Aucun résultat à exporter. Veuillez d'abord lancer la planification."
            )
            return
        
        # Check at least one option selected
        if not any([
            self.export_excel_cb.isChecked(),
            self.export_word_cb.isChecked(),
            self.export_stats_cb.isChecked()
        ]):
            QMessageBox.warning(
                self, 
                "Attention", 
                "⚠️ Veuillez sélectionner au moins une option d'export."
            )
            return
        
        # Build export config
        export_config = {
            'output_dir': export_path,
            'result': self.last_result,
            'options': {
                'excel': self.export_excel_cb.isChecked(),
                'word': self.export_word_cb.isChecked(),
                'stats': self.export_stats_cb.isChecked()
            }
        }
        
        # Emit signal to trigger export
        self.export_requested.emit(export_config)
