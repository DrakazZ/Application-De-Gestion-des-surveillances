# home_page.py
# ------------------------------------------------------
# Main Home (Accueil) Page
# ------------------------------------------------------
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QMessageBox, QProgressBar
)
from PyQt5.QtCore import Qt, pyqtSignal
from ui.widgets.grade_panel import GradePanel
from ui.widgets.export_panel import ExportPanel
from ui.widgets.data_input_panel import DataInputPanel
from ui.widgets.dashboard_panel import DashboardPanel
from ui.styles.style import apply_shadow_effect
from workers.backend_worker import SchedulerWorker, ValidationWorker
import pandas as pd
from core.export_docs import export_surveillance_documents  
import os


class HomePage(QWidget):
    """Main landing page for ISI application"""

    generation_complete = pyqtSignal(dict)

    def __init__(self, parent=None, show_top_bar=True):
        super().__init__(parent)
        self.show_top_bar = show_top_bar
        self.worker = None
        self.result_data = None
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

        # === DASHBOARD ===
        dashboard_frame = QFrame()
        dashboard_frame.setObjectName("elevatedPanel")
        dashboard_layout = QVBoxLayout(dashboard_frame)
        dashboard_layout.setContentsMargins(16, 16, 16, 16)
        self.dashboard_panel = DashboardPanel()
        dashboard_layout.addWidget(self.dashboard_panel)
        apply_shadow_effect(dashboard_frame)

        # === PROGRESS BAR ===
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        root_layout.addWidget(self.progress_bar)

        # === ASSEMBLE ===
        root_layout.addLayout(content)
        root_layout.addWidget(dashboard_frame)
        self.setLayout(root_layout)
        self.ExportPanel.export_requested.connect(self.handle_export_request)

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

        # Stats display
        if 'stats' in result:
            self.dashboard_panel.update_stats(result['stats'])
        
        # Unwrap hybrid result
        hybrid_result = result.get('result', result)

        # Build assignment DataFrame for later exports
        df = self._build_assignment_dataframe(hybrid_result)
        if df is not None:
            result['final_df'] = df


        # Enable export panel but do not export anything
        self.ExportPanel.set_result(result)
        self.ExportPanel.path_field.setText(self.output_dir)
        self.ExportPanel.export_btn.setEnabled(True)


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
        """Build simplified DataFrame for Word export (Date, Time, Teacher)."""
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
                    teacher = teachers[t_idx].get('name', 'Inconnu')
                    assignments.append({
                        'Date': date,
                        'Time': time,
                        'Teacher': teacher
                    })

            return pd.DataFrame(assignments)

        except Exception as e:
            print(f"[ERROR] Failed to build assignment DataFrame: {e}")
            return None
