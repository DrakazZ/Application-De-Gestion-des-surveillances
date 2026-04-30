from PyQt5.QtWidgets import (
    QLineEdit, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QMessageBox,
    QGroupBox, QFormLayout, QFileDialog, QFrame, QLabel, QSpinBox, QDateEdit, QTimeEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
import pandas as pd
from ui.styles.style import apply_shadow_effect
from ui.widgets.modify_dashboard_panel import SimpleDashboardPanel
from workers.db_handler import DBHandler

textsize = "7pt"
labelsize = "9pt"
titlesize = "11pt"
class ModifyPage(QWidget):
    imported = pyqtSignal(pd.DataFrame)  # Signal emits the imported DataFrame

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_handler = DBHandler()
        self.setup_ui()

    def setup_ui(self):
        # === ROOT LAYOUT ===
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(20)

        # === MAIN CONTENT ZONE ===
        content = QHBoxLayout()
        content.setSpacing(15)

        # Left side — configuration & input panels
        left_col = QVBoxLayout()
        left_col.setSpacing(16)
        import_export_panel = self.create_export_import_panel()
        left_col.addWidget(import_export_panel)


        left_frame = QFrame()
        left_frame.setObjectName("basePanel")
        left_frame.setLayout(left_col)
        apply_shadow_effect(left_frame)

        # Right side — grading config
        right_col = QHBoxLayout()
        right_col.setSpacing(16)

        exchange_panel = self.create_exchange_panel()
        raport_panel = self.create_raport_panel()

        right_col.addWidget(raport_panel)
        right_col.addWidget(exchange_panel)
        
        right_frame = QFrame()
        right_frame.setObjectName("basePanel")
        right_frame.setLayout(right_col)
        apply_shadow_effect(right_frame)

        content.addWidget(left_frame, 1)
        content.addWidget(right_frame, 2)

        # === DASHBOARD (Bottom Section) ===
        dashboard_frame = QFrame()
        dashboard_frame.setObjectName("elevatedPanel")
        dashboard_layout = QVBoxLayout(dashboard_frame)
        dashboard_layout.setContentsMargins(16, 16, 16, 16)

        self.dashboard_panel = SimpleDashboardPanel()
        dashboard_layout.addWidget(self.dashboard_panel)

        apply_shadow_effect(dashboard_frame)

        # === ASSEMBLE EVERYTHING ===
        root_layout.addLayout(content)
        root_layout.addWidget(dashboard_frame)

        self.setLayout(root_layout)

    def create_raport_panel(self):
        panel = QFrame()
        panel.setObjectName("basePanel")
        apply_shadow_effect(panel)

        main_layout = QVBoxLayout(panel)
        main_layout.setContentsMargins(8, 4, 8, 4)
        main_layout.setSpacing(8)

        title = QLabel("📝 Rapporter des sessions")
        title.setObjectName("sectionLabel")
        title.setStyleSheet(f"font-size: {titlesize}; font-weight: bold;")
        main_layout.addWidget(title)

        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(6)

        self.report_prof_id = QSpinBox()
        self.report_prof_id.setRange(0, 999999)

        self.report_date = QDateEdit()
        self.report_date.setCalendarPopup(True)

        self.report_time = QTimeEdit()

        form_layout.addRow(QLabel("ID enseignant:"), self.report_prof_id)
        form_layout.addRow(QLabel("Date:"), self.report_date)
        form_layout.addRow(QLabel("Heure:"), self.report_time)

        main_layout.addLayout(form_layout)

        report_btn = QPushButton("Rapporter")
        report_btn.setObjectName("primaryButton")
        report_btn.setFixedHeight(30)
        report_btn.clicked.connect(self.handle_report)
        main_layout.addWidget(report_btn, alignment=Qt.AlignCenter)

        return panel  # ✅ return QWidget, not layout

    def handle_report(self):
        prof = self.report_prof_id.value()
        date = self.report_date.date().toString("yyyy-MM-dd")
        time = self.report_time.time().toString("HH:mm")

        # db_handler.mark_session_reported(prof, date, time)
        print(f"Reported session for {prof}")

    def create_export_import_panel(self):
        panel = QFrame()
        panel.setObjectName("basePanel")
        apply_shadow_effect(panel)

        main_layout = QVBoxLayout(panel)
        main_layout.setContentsMargins(8, 4, 8, 4)
        main_layout.setSpacing(8)

        # === Title ===
        title = QLabel("💾 Modifier manuellement la base de données")
        title.setObjectName("sectionLabel")
        title.setStyleSheet(f"font-size: {titlesize}; font-weight: bold;")
        main_layout.addWidget(title)

        # === Buttons ===

        import_btn = QPushButton("Importer")
        import_btn.setObjectName("primaryButton")
        import_btn.setFixedHeight(20)
        import_btn.clicked.connect(self.handle_import)

        # Add buttons to layout with spacing
        main_layout.addWidget(import_btn, alignment=Qt.AlignCenter)

        return panel

    def handle_import(self):
        path, _ = QFileDialog.getOpenFileName(self, "Importer le fichier", "", "Excel Files (*.xlsx)")
        if not path:
            return

        if not path.lower().endswith('.xlsx'):
            QMessageBox.warning(self, "Erreur", "Le fichier doit être un .xlsx")
            return

        try:
            self.db_handler.import_from_excel(path)

            # ✅ Show success message
            QMessageBox.information(
                self,
                "Succès",
                f"Base importée avec succès depuis:\n{path}\n"
                f"{len(self.db_handler.data)} lignes importées."
            )

            # Emit the imported signal with the DataFrame
            self.imported.emit(self.db_handler.data)

        except ValueError as e:
            QMessageBox.critical(self, "Erreur", str(e))


    def create_exchange_panel(self):
        panel = QFrame()
        panel.setObjectName("basePanel")
        apply_shadow_effect(panel)

        main_layout = QVBoxLayout(panel)
        main_layout.setContentsMargins(8, 4, 8, 4)
        main_layout.setSpacing(4)

        # === Title ===
        title = QLabel("🔄 Échanger des enseignants")
        title.setObjectName("sectionLabel")
        title.setStyleSheet(f"font-size: {titlesize}; font-weight: bold;")
        main_layout.addWidget(title)

       # === Form ===
        form_layout = QHBoxLayout()  # horizontal container for the two columns
        form_layout.setSpacing(20)

        # ---------- Left column (Prof 1) ----------
        left_col = QVBoxLayout()
        left_col.setSpacing(6)

        self.prof1_id = QSpinBox()
        self.prof1_id.setRange(0, 999999)  # adjust max ID as needed

        self.prof1_date = QDateEdit()
        self.prof1_date.setCalendarPopup(True)

        self.prof1_time = QTimeEdit()

        left_col.addWidget(QLabel("ID enseignant 1:"))
        left_col.addWidget(self.prof1_id)
        left_col.addWidget(QLabel("Date:"))
        left_col.addWidget(self.prof1_date)
        left_col.addWidget(QLabel("Heure:"))
        left_col.addWidget(self.prof1_time)

        # ---------- Right column (Prof 2) ----------
        right_col = QVBoxLayout()
        right_col.setSpacing(6)

        self.prof2_id = QSpinBox()
        self.prof2_id.setRange(0, 999999)

        self.prof2_date = QDateEdit()
        self.prof2_date.setCalendarPopup(True)

        self.prof2_time = QTimeEdit()

        right_col.addWidget(QLabel("ID enseignant 2:"))
        right_col.addWidget(self.prof2_id)
        right_col.addWidget(QLabel("Date:"))
        right_col.addWidget(self.prof2_date)
        right_col.addWidget(QLabel("Heure:"))
        right_col.addWidget(self.prof2_time)

        # Add both columns to the horizontal form layout
        form_layout.addLayout(left_col)
        form_layout.addLayout(right_col)

        # Add the form to the main panel layout
        main_layout.addLayout(form_layout)
        # === Exchange button ===
        swap_btn = QPushButton("Échanger")
        swap_btn.setObjectName("primaryButton")
        swap_btn.setStyleSheet(f"font-size: {textsize};")
        swap_btn.setFixedHeight(30)
        swap_btn.clicked.connect(self.handle_exchange)

        main_layout.addWidget(swap_btn, alignment=Qt.AlignCenter)

        return panel


    def handle_exchange(self):
        id1 = self.prof1_id.value()  # Changed from .text() to .value()
        id2 = self.prof2_id.value()
        date1 = self.prof1_date.date().toString("yyyy-MM-dd")
        time1 = self.prof1_time.time().toString("HH:mm")
        date2 = self.prof2_date.date().toString("yyyy-MM-dd")
        time2 = self.prof2_time.time().toString("HH:mm")
        
        self.db_handler.swap_sessions(id1, id2)
        print(f"Swapped: Prof {id1} ({date1} {time1}) ↔ Prof {id2} ({date2} {time2})")
