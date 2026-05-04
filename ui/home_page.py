# home_page.py
# ------------------------------------------------------
# Main Home (Accueil) Page
# ------------------------------------------------------
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QMessageBox, QProgressBar,
    QFormLayout, QFileDialog, QLabel, QPushButton, QSpinBox, QDateEdit, QTimeEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
from ui.widgets.grade_panel import GradePanel
from ui.widgets.export_panel import ExportPanel
from ui.widgets.data_input_panel import DataInputPanel
from ui.styles.style import apply_shadow_effect
from workers.backend_worker import SchedulerWorker, ValidationWorker
import pandas as pd
from core.export_docs import export_surveillance_documents  
import os
import re


class HomePage(QWidget):
    """Main landing page for ISI application"""

    generation_complete = pyqtSignal(dict)

    def __init__(self, parent=None, show_top_bar=True):
        super().__init__(parent)
        self.show_top_bar = show_top_bar
        self.worker = None
        self.result_data = None
        self.final_df = None
        self.reported_counts = {}
        self.output_dir = "data/output"
        os.makedirs(self.output_dir, exist_ok=True)

        self.setup_ui()

    # ====================================================
    # UI SETUP
    # ====================================================
    def setup_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(20)

        # === MAIN CONTENT ===
        content = QHBoxLayout()
        content.setSpacing(15)

        # Left — Export panel
        left_col = QVBoxLayout()
        left_col.setSpacing(16)
        self.ExportPanel = ExportPanel()
        left_col.addWidget(self.ExportPanel)

        left_frame = QFrame()
        left_frame.setObjectName("basePanel")
        left_frame.setLayout(left_col)
        apply_shadow_effect(left_frame)

        # Right — Grade + Data panels
        right_col = QHBoxLayout()
        right_col.setSpacing(16)
        self.grade_panel = GradePanel()
        self.data_panel = DataInputPanel()
        right_col.addWidget(self.grade_panel)
        right_col.addWidget(self.data_panel)
        self.data_panel.import_requested.connect(self.validate_and_run)

        right_frame = QFrame()
        right_frame.setObjectName("basePanel")
        right_frame.setLayout(right_col)
        apply_shadow_effect(right_frame)

        content.addWidget(left_frame, 1)
        content.addWidget(right_frame, 2)

        # === BOTTOM ROW ===
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(16)
        self.import_panel = self.create_import_panel()
        self.report_panel = self.create_report_panel()
        self.exchange_panel = self.create_exchange_panel()
        bottom_row.addWidget(self.import_panel, 1)
        bottom_row.addWidget(self.report_panel, 1)
        bottom_row.addWidget(self.exchange_panel, 2)

        # === PROGRESS BAR ===
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        root_layout.addWidget(self.progress_bar)

        # === ASSEMBLE ===
        root_layout.addLayout(content)
        root_layout.addLayout(bottom_row)
        self.setLayout(root_layout)

        # Connect signal
        self.ExportPanel.export_requested.connect(self.handle_export_request)

    # ====================================================
    # BOTTOM ROW PANELS
    # ====================================================
    def create_import_panel(self):
        panel = QFrame()
        panel.setObjectName("basePanel")
        apply_shadow_effect(panel)

        main_layout = QVBoxLayout(panel)
        main_layout.setContentsMargins(8, 4, 8, 4)
        main_layout.setSpacing(8)

        title = QLabel("Modifier manuellement la base de données")
        title.setObjectName("sectionLabel")
        main_layout.addWidget(title)

        import_btn = QPushButton("Importer")
        import_btn.setObjectName("primaryButton")
        import_btn.setFixedHeight(30)
        import_btn.clicked.connect(self.handle_import)
        main_layout.addWidget(import_btn, alignment=Qt.AlignCenter)

        return panel

    def create_report_panel(self):
        panel = QFrame()
        panel.setObjectName("basePanel")
        apply_shadow_effect(panel)

        main_layout = QVBoxLayout(panel)
        main_layout.setContentsMargins(8, 4, 8, 4)
        main_layout.setSpacing(8)

        title = QLabel("Rapporter des sessions")
        title.setObjectName("sectionLabel")
        main_layout.addWidget(title)

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

        return panel

    def create_exchange_panel(self):
        panel = QFrame()
        panel.setObjectName("basePanel")
        apply_shadow_effect(panel)

        main_layout = QVBoxLayout(panel)
        main_layout.setContentsMargins(8, 4, 8, 4)
        main_layout.setSpacing(4)

        title = QLabel("Échanger des enseignants")
        title.setObjectName("sectionLabel")
        main_layout.addWidget(title)

        form_layout = QHBoxLayout()
        form_layout.setSpacing(20)

        left_col = QVBoxLayout()
        left_col.setSpacing(6)

        self.prof1_id = QSpinBox()
        self.prof1_id.setRange(0, 999999)

        self.prof1_date = QDateEdit()
        self.prof1_date.setCalendarPopup(True)

        self.prof1_time = QTimeEdit()

        left_col.addWidget(QLabel("ID enseignant 1:"))
        left_col.addWidget(self.prof1_id)
        left_col.addWidget(QLabel("Date:"))
        left_col.addWidget(self.prof1_date)
        left_col.addWidget(QLabel("Heure:"))
        left_col.addWidget(self.prof1_time)

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

        form_layout.addLayout(left_col)
        form_layout.addLayout(right_col)

        main_layout.addLayout(form_layout)

        swap_btn = QPushButton("Échanger")
        swap_btn.setObjectName("primaryButton")
        swap_btn.setFixedHeight(30)
        swap_btn.clicked.connect(self.handle_exchange)
        main_layout.addWidget(swap_btn, alignment=Qt.AlignCenter)

        return panel

    # ====================================================
    # BOTTOM ROW HANDLERS
    # ====================================================
    def handle_import(self):
        path, _ = QFileDialog.getOpenFileName(self, "Importer le fichier", "", "Excel Files (*.xlsx)")
        if not path:
            return

        if not path.lower().endswith('.xlsx'):
            QMessageBox.warning(self, "Erreur", "Le fichier doit être un .xlsx")
            return

        try:
            df = pd.read_excel(path)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de lire le fichier:\n{e}")
            return

        df = df.copy()
        if hasattr(df.columns, "str"):
            df.columns = df.columns.str.strip()

        required_cols = ["Date", "Time", "Teacher"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            QMessageBox.critical(
                self,
                "Erreur",
                "Colonnes manquantes: " + ", ".join(missing_cols)
            )
            return

        if "TeacherId" not in df.columns:
            df["TeacherId"] = ""
            QMessageBox.warning(
                self,
                "Attention",
                "La colonne TeacherId est absente. Les échanges et rapports nécessitent un ID."
            )

        df["Teacher"] = df["Teacher"].fillna("").astype(str).str.strip()
        df["TeacherId"] = df["TeacherId"].apply(self._normalize_teacher_id)
        df["Date"] = df["Date"].apply(self._normalize_date_value)
        df["Time"] = df["Time"].apply(self._normalize_time_value)

        self.final_df = df
        self.reported_counts = {}
        self.result_data = {'final_df': df}
        self._set_result_dataframe(df)

        QMessageBox.information(
            self,
            "Succès",
            f"Base importée avec succès depuis:\n{path}\n{len(df)} lignes importées."
        )

    def handle_exchange(self):
        if not self._ensure_final_df():
            return

        if "TeacherId" not in self.final_df.columns:
            QMessageBox.critical(self, "Erreur", "La colonne TeacherId est requise pour échanger.")
            return

        id1 = self._normalize_teacher_id(self.prof1_id.value())
        id2 = self._normalize_teacher_id(self.prof2_id.value())

        if not id1 or id1 == "0" or not id2 or id2 == "0":
            QMessageBox.warning(self, "Attention", "Veuillez saisir deux IDs enseignants valides.")
            return

        idxs1 = self._find_matching_indices(self.final_df, id1, self.prof1_date, self.prof1_time)
        idxs2 = self._find_matching_indices(self.final_df, id2, self.prof2_date, self.prof2_time)

        if len(idxs1) != 1 or len(idxs2) != 1:
            QMessageBox.warning(
                self,
                "Attention",
                "Aucune session unique trouvée pour les critères fournis."
            )
            return

        idx1 = idxs1[0]
        idx2 = idxs2[0]
        for col in ["Teacher", "TeacherId"]:
            self.final_df.at[idx1, col], self.final_df.at[idx2, col] = (
                self.final_df.at[idx2, col],
                self.final_df.at[idx1, col]
            )

        self._set_result_dataframe(self.final_df)

        QMessageBox.information(self, "Succès", "Échange effectué avec succès.")

    def handle_report(self):
        if not self._ensure_final_df():
            return

        if "TeacherId" not in self.final_df.columns:
            QMessageBox.critical(self, "Erreur", "La colonne TeacherId est requise pour reporter.")
            return

        teacher_id = self._normalize_teacher_id(self.report_prof_id.value())
        if not teacher_id or teacher_id == "0":
            QMessageBox.warning(self, "Attention", "Veuillez saisir un ID enseignant valide.")
            return

        idxs = self._find_matching_indices(self.final_df, teacher_id, self.report_date, self.report_time)
        if not idxs:
            QMessageBox.warning(self, "Attention", "Aucune session correspondante trouvée.")
            return

        removed_count = len(idxs)
        self.final_df = self.final_df.drop(index=idxs).reset_index(drop=True)
        self.reported_counts[teacher_id] = self.reported_counts.get(teacher_id, 0) + removed_count
        self._write_reported_counts()
        self._set_result_dataframe(self.final_df)

        QMessageBox.information(
            self,
            "Succès",
            f"{removed_count} session(s) rapportée(s) pour l'enseignant {teacher_id}."
        )

    def _ensure_final_df(self):
        if self.final_df is None or self.final_df.empty:
            QMessageBox.warning(
                self,
                "Attention",
                "Veuillez générer ou importer un planning avant de modifier."
            )
            return False
        return True

    def _set_result_dataframe(self, df):
        if self.result_data is None:
            self.result_data = {}
        self.result_data['final_df'] = df
        self.ExportPanel.set_result(self.result_data)
        self.ExportPanel.path_field.setText(self.output_dir)
        self.ExportPanel.export_btn.setEnabled(True)

    def _normalize_teacher_id(self, value):
        if pd.isna(value):
            return ""
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value).strip()

    def _normalize_date_value(self, value):
        s = str(value).strip()
        for pattern in (r"\d{2}/\d{2}/\d{4}", r"\d{4}-\d{2}-\d{2}", r"\d{2}/\d{2}"):
            match = re.search(pattern, s)
            if match:
                return match.group(0)
        return s

    def _normalize_time_value(self, value):
        s = str(value).strip()
        match = re.search(r"\d{2}:\d{2}", s)
        return match.group(0) if match else s

    def _date_variants(self, qdate):
        variants = [
            qdate.date().toString("dd/MM"),
            qdate.date().toString("dd/MM/yyyy"),
            qdate.date().toString("yyyy-MM-dd"),
        ]
        return list(dict.fromkeys(self._normalize_date_value(v) for v in variants))

    def _find_matching_indices(self, df, teacher_id, date_edit, time_edit):
        teacher_id = self._normalize_teacher_id(teacher_id)
        date_variants = set(self._date_variants(date_edit))
        time_value = self._normalize_time_value(time_edit.time().toString("HH:mm"))

        df_teacher = df["TeacherId"].apply(self._normalize_teacher_id)
        df_date = df["Date"].apply(self._normalize_date_value)
        df_time = df["Time"].apply(self._normalize_time_value)

        mask = df_teacher == teacher_id
        mask &= df_date.isin(date_variants)
        mask &= df_time == time_value

        return df.index[mask].tolist()

    def _write_reported_counts(self):
        if not self.reported_counts:
            return

        rows = [
            {"Teacher": teacher_id, "Count": count}
            for teacher_id, count in sorted(self.reported_counts.items())
        ]
        report_df = pd.DataFrame(rows)
        report_path = os.path.join(self.output_dir, "reported_sessions.csv")
        report_df.to_csv(report_path, index=False)

    # ====================================================
    # STEP 1 — VALIDATION & RUN
    # ====================================================
    def validate_and_run(self, files):
        """Triggered when Import is clicked."""

        # --- Stop previous worker if still running ---
        if hasattr(self, 'validation_worker') and self.validation_worker is not None:
            if self.validation_worker.isRunning():
                self.validation_worker.terminate()  # safely stop short-running worker
                self.validation_worker.wait()

        # --- Check all files ---
        missing = [k for k, v in files.items() if not v]
        if missing:
            QMessageBox.warning(
                self,
                "Fichiers manquants",
                f"Veuillez sélectionner tous les fichiers:\n{', '.join(missing)}"
            )
            return

        # --- Check grade limits ---
        if not self.grade_panel.rank_limits or len(self.grade_panel.rank_limits) < len(self.grade_panel.ranks):
            QMessageBox.warning(
                self,
                "Limites incomplètes",
                "Veuillez définir les limites pour tous les grades avant d’importer."
            )
            return

        # --- Get GA settings (persist last values) ---
        print("DEBUG: Current GA settings in Data Panel:", self.data_panel.ga_settings)

        ga_settings = self.data_panel.ga_settings
        population = ga_settings['population']
        generations = ga_settings['generations']

        config = {
            'use_ga': True,
            'population': population,
            'generations': generations,
            'grade_limits': self.grade_panel.rank_limits
        }

        # --- Start validation worker ---
        self.validation_worker = ValidationWorker(files, config)
        self.validation_worker.finished.connect(self.on_validation_complete)
        self.validation_worker.start()

        # --- Update UI ---
        self.data_panel.import_btn.setEnabled(False)
        self.data_panel.import_btn.setText("Validation...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate bar


    # ====================================================
    # STEP 2 — VALIDATION COMPLETE
    # ====================================================
    def on_validation_complete(self, result):
        self.progress_bar.setVisible(False)
        self.data_panel.import_btn.setEnabled(True)

        if not result['valid']:
            error_msg = "Erreurs de validation:\n\n" + "\n".join(result['errors'])
            if result['warnings']:
                error_msg += "\n\nAvertissements:\n" + "\n".join(result['warnings'])
            QMessageBox.critical(self, "Validation échouée", error_msg)
            return

        if result['warnings']:
            QMessageBox.warning(
                self,
                "Avertissements",
                "\n".join(result['warnings']) + "\n\nContinuer quand même?"
            )

        self.run_generation(result['files'])

    # ====================================================
    # STEP 3 — RUN GENERATION
    # ====================================================
    def run_generation(self, files):
        """Run the scheduling algorithm"""
        ga_settings = getattr(self.data_panel, 'ga_settings', {})
        population = ga_settings.get('population', 70)
        generations = ga_settings.get('generations', 300)

        config = {
            'max_sessions': 7,
            'use_ga': True,
            'population': population,      # now dynamic
            'generations': generations,    # now dynamic
            'grade_limits': self.grade_panel.rank_limits
        }

        self.worker = SchedulerWorker(files, config, self.output_dir)
        self.worker.progress_update.connect(self.on_progress)
        self.worker.stage_update.connect(self.on_stage)
        self.worker.finished.connect(self.on_generation_complete)
        self.worker.error.connect(self.on_error)

        self.data_panel.import_btn.setEnabled(False)
        self.data_panel.import_btn.setText("Génération en cours...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.worker.start()

    # ====================================================
    # STEP 4 — PROGRESS CALLBACKS
    # ====================================================
    def on_progress(self, message, percent):
        self.progress_bar.setValue(percent)
        self.progress_bar.setFormat(f"{message} ({percent}%)")

    def on_stage(self, stage_name):
        print(f"Stage: {stage_name}")

    def on_generation_complete(self, result):
        self.result_data = result  # store results in memory only
        self.progress_bar.setVisible(False)
        self.data_panel.import_btn.setEnabled(True)
        self.data_panel.import_btn.setText("Importer")
        
        # Unwrap hybrid result
        hybrid_result = result.get('result', result)

        # Build assignment DataFrame for later exports
        df = self._build_assignment_dataframe(hybrid_result)
        if df is not None:
            result['final_df'] = df
            self.final_df = df
            self.reported_counts = {}
            self._set_result_dataframe(df)


    def on_error(self, error_msg):
        self.progress_bar.setVisible(False)
        self.data_panel.import_btn.setEnabled(True)
        self.data_panel.import_btn.setText("Importer")
        QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite:\n\n{error_msg}")

    # ====================================================
    # STEP 5 — HANDLE EXPORT REQUEST
    # ====================================================
    def handle_export_request(self, export_config):
        """Handles final export depending on selected options."""
        result = export_config['result']
        output_dir = export_config['output_dir']
        options = export_config['options']

        if options.get('excel'):
            self.export_to_excel(result, output_dir)

        if options.get('word'):
            self.export_to_word(result, output_dir)

        if options.get('stats'):
            self.export_stats(result, output_dir)

        QMessageBox.information(self, "Export terminé", f"Documents exportés vers:\n{output_dir}")

    def export_to_excel(self, result, output_dir):

        df = result.get('final_df')  # depends on your data structure
        if df is not None:
            excel_path = os.path.join(output_dir, "Planning_Final.xlsx")
            df.to_excel(excel_path, index=False)

    def export_to_word(self, result, output_dir):   
        df = result.get('final_df')  # same DataFrame
        if df is not None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            template_dir = os.path.join(base_dir, "..", "data", "templates")
            export_surveillance_documents(df, output_dir, template_dir=template_dir)

    def export_stats(self, result, output_dir):
        stats = result.get('stats', {})
        with open(os.path.join(output_dir, "stats_summary.txt"), "w", encoding="utf-8") as f:
            for k, v in stats.items():
                f.write(f"{k}: {v}\n")

    # ====================================================
    # STEP 6 — HELPER: BUILD ASSIGNMENT DATAFRAME
    # ====================================================
    def _build_assignment_dataframe(self, hybrid_result):
        """Build simplified DataFrame for Word export (Date, Time, Teacher, TeacherId)."""
        try:
            assignments = []
            sessions = hybrid_result.get('sessions', [])
            teachers = hybrid_result.get('teachers', [])
            final_assignment = hybrid_result.get('final_assignment', {})

            for session in sessions:
                session_id = session.get('id')
                date = session.get('date')
                time = session.get('time')
                assigned_indices = final_assignment.get(session_id, [])

                for t_idx in assigned_indices:
                    teacher = teachers[t_idx]
                    teacher_name = teacher.get('name', 'Inconnu')
                    teacher_id = teacher.get('id')
                    teacher_id = '' if teacher_id is None else str(teacher_id)
                    assignments.append({
                        'Date': date,
                        'Time': time,
                        'Teacher': teacher_name,
                        'TeacherId': teacher_id
                    })

            return pd.DataFrame(assignments)

        except Exception as e:
            print(f"[ERROR] Failed to build assignment DataFrame: {e}")
            return None
