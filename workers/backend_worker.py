"""
Backend Worker - Runs scheduling algorithm in separate thread
Communicates with UI via Qt signals
"""
from PyQt5.QtCore import QThread, pyqtSignal
import pandas as pd
import traceback
import time
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core import (
    preprocess_exam_info,
    preprocess_professors,
    solve_hybrid,
    HybridConfig,
    SchedulerConfig
)


class SchedulerWorker(QThread):
    """Worker thread for running scheduling algorithm"""
    
    # Signals for UI communication
    progress_update = pyqtSignal(str, int)  # (message, percentage)
    stage_update = pyqtSignal(str)  # Stage name
    finished = pyqtSignal(dict)  # Results dictionary
    error = pyqtSignal(str)  # Error message
    
    def __init__(self, files, config, output_dir):
        super().__init__()
        self.files = files
        self.config = config
        self.output_dir = output_dir
        self.is_cancelled = False
        
    def run(self):
        """Main execution in separate thread"""
        try:
            result = self._execute_pipeline()
            if not self.is_cancelled:
                self.finished.emit(result)
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}\n\n{traceback.format_exc()}"
            self.error.emit(error_msg)
    
    def cancel(self):
        """Request cancellation"""
        self.is_cancelled = True
    
    def _execute_pipeline(self):
        """Execute full scheduling pipeline with progress updates"""
        
        # ========== STEP 1: Process Exam Data ==========
        self.stage_update.emit("Processing Exam Data...")
        self.progress_update.emit("Loading room assignments", 10)
        self.msleep(50)
        
        profs_by_session, rooms_by_session, df_info = preprocess_exam_info(
            self.files['salles'],
        )

        if df_info is None or df_info.empty:
            df_calendar = pd.DataFrame(columns=[
                "Date", "Time_Start", "Time_End", "Subject", "Class"
            ])
        else:
            df_calendar = pd.DataFrame({
                "Date": df_info["dateExam"],
                "Time_Start": df_info["h_debut"],
                "Time_End": df_info["h_fin"],
                "Subject": [""] * len(df_info),
                "Class": [""] * len(df_info)
            })
            df_calendar = df_calendar.sort_values(
                by=["Date", "Time_Start", "Class"]
            ).reset_index(drop=True)
        
        if self.is_cancelled:
            return None
        
        self.progress_update.emit(
            f"Found {len(df_calendar)} exam sessions",
            20
        )
        self.msleep(50)

        # ========== STEP 2: Load Professors ==========
        self.stage_update.emit("Loading Professors...")
        self.progress_update.emit("Reading professor data and wishes", 40)
        self.msleep(50)
        
        df_profs = preprocess_professors(
            self.files['professeurs'],
            self.files['souhaits']
        )
        
        if self.is_cancelled:
            return None
        
        self.progress_update.emit(
            f"Loaded {len(df_profs)} professors",
            50
        )
        self.msleep(50)
        
        # ========== STEP 4: Configure Solver ==========
        self.stage_update.emit("Configuring Solver...")
        
        greedy_config = SchedulerConfig(
            min_per_room=2,
            padding_percentage=0.10,
            default_max_sessions=self.config.get('max_sessions', 7),
            respect_wishes=True,
            prefer_responsible=True,
            balance_grades=True,
            use_lookahead=True,
            use_two_phase=True
        )
        
        hybrid_config = HybridConfig(
            greedy_config=greedy_config,
            population_size=self.config.get('population', 70),
            generations=self.config.get('generations', 300),
            crossover_rate=0.8,
            mutation_rate=0.1,
            elitism_count=5,
            tournament_size=3,
            verbose=False,  # Suppress console output
            use_ga=self.config.get('use_ga', True)
        )
        
        # ========== STEP 5: Run Solver ==========
        self.stage_update.emit("Running Algorithm...")
        self.progress_update.emit("Generating schedule (this may take a while)", 60)
        self.msleep(50)

        # Create progress callback for GA
        def ga_progress(stage, info):
            if self.is_cancelled:
                return True

            if stage == 'greedy':
                msg = f"Greedy phase - {info.get('stage', '')}"
                percent = int(info.get('progress', 0) * 0.6)  # up to 60%
            elif stage == 'ga':
                gen = info.get('generation', 0)
                best_fit = info.get('best_fitness', 0)
                percent = 60 + int((info.get('progress', 0) / 100) * 30)
                msg = f"GA generation {gen} - Fitness {best_fit:.2f}"
            else:
                msg = f"Stage: {stage}"
                percent = 0

            self.progress_update.emit(msg, percent)
            return False
        
        result = solve_hybrid(
            df_calendar=df_calendar,
            df_profs=df_profs,
            profs_by_session=profs_by_session,
            rooms_by_session=rooms_by_session,
            config=hybrid_config,
            provided_ui_grade_limits=self.config.get('grade_limits', None),
            progress_callback=ga_progress
        )
        
        if self.is_cancelled:
            return None
        
        # Return result with file paths
        return {
            'result': result,
            """'output_prefix': output_prefix,
            'timestamp': timestamp,"""
            'stats': {
                'total_sessions': len(df_calendar),
                'total_profs': len(df_profs),
                'violations': len(result['final_chromosome'].violations),
                'fitness': result['final_chromosome'].fitness_score
            }
        }

class ValidationWorker(QThread):
    """Quick validation worker - checks files before processing"""
    
    finished = pyqtSignal(dict)  # {valid: bool, errors: list}

    def __init__(self, files, config):
        super().__init__()
        self.files = files
        self.config = config
    
    def run(self):
        """Validate input files"""
        import pandas as pd
        
        errors = []
        warnings = []
        missing_entries = {
            'professeurs': [],
            'souhaits': [],
            'salles': []
        }

        def row_snapshot(row):
            data = {}
            for key, value in row.to_dict().items():
                if pd.isna(value):
                    data[key] = ""
                else:
                    data[key] = str(value)
            return data
        
        try:
            # Check professors Excel
            if not os.path.exists(self.files['professeurs']):
                errors.append("Professors Excel not found")
            else:
                try:
                    df = pd.read_excel(self.files['professeurs'])
                    required_cols = [
                        'nom_ens',
                        'prenom_ens',
                        'grade_code_ens',
                        'code_smartex_ens',
                        'participe_surveillance'
                    ]
                    missing = [c for c in required_cols if c not in df.columns]
                    if missing:
                        errors.append(f"Professors file missing columns: {missing}")
                        raise ValueError("Missing required columns")
                    
                    for idx, row in df.iterrows():
                        participe = str(row.get('participe_surveillance', '')).strip().lower() == 'true'
                        missing_cols = [c for c in required_cols if pd.isnull(row[c]) or str(row[c]).strip() == ""]
                        if missing_cols:
                            for col in missing_cols:
                                if col == 'code_smartex_ens' and not participe:
                                    continue
                                missing_entries['professeurs'].append({
                                    'row': int(idx),
                                    'column': col,
                                    'row_data': row_snapshot(row)
                                })

                    if not missing_entries['professeurs']:
                        participe_mask = (
                            df['participe_surveillance']
                            .astype(str)
                            .str.lower()
                            .str.strip() == 'true'
                        )
                        codes = df.loc[participe_mask, 'code_smartex_ens']
                        code_str = codes.astype(str).str.strip()
                        valid_mask = ~code_str.isin(['', 'nan', 'none'])
                        dup_mask = code_str[valid_mask].duplicated(keep=False)
                        if dup_mask.any():
                            dup_values = code_str[valid_mask][dup_mask].unique().tolist()
                            errors.append(f"Duplicate teacher IDs found: {dup_values}")
                except Exception as e:
                    errors.append(f"Cannot read professors file: {e}")
            
            # Check wishes Excel
            if not os.path.exists(self.files['souhaits']):
                warnings.append("Wishes file not found ")
            else:
                try:
                    df = pd.read_excel(self.files['souhaits'])
                    required_cols = ["Enseignant", "Jour", "Séances"]
                    missing = [c for c in required_cols if c not in df.columns]
                    if missing:
                        errors.append(f"Wishes file missing columns: {missing}")

                    # Check for empty cells
                    for idx, row in df.iterrows():
                        missing_cols = [c for c in required_cols if pd.isnull(row[c]) or str(row[c]).strip() == ""]
                        if missing_cols:
                            for col in missing_cols:
                                missing_entries['souhaits'].append({
                                    'row': int(idx),
                                    'column': col,
                                    'row_data': row_snapshot(row)
                                })

                except Exception as e:
                    errors.append(f"Cannot read wishes file: {e}")

            # Check rooms Excel
            if not os.path.exists(self.files['salles']):
                errors.append("Rooms assignment file not found")
            else:
                try:
                    df = pd.read_excel(self.files['salles'])
                    required_cols = ["enseignant", "dateExam", "h_debut", "h_fin"]
                    missing = [c for c in required_cols if c not in df.columns]
                    if missing:
                        errors.append(f"Rooms file missing columns: {missing}")
                    
                    # Check for empty cells
                    for idx, row in df.iterrows():
                        missing_cols = [c for c in required_cols if pd.isnull(row[c]) or str(row[c]).strip() == ""]
                        if missing_cols:
                            for col in missing_cols:
                                missing_entries['salles'].append({
                                    'row': int(idx),
                                    'column': col,
                                    'row_data': row_snapshot(row)
                                })
                except Exception as e:
                    errors.append(f"Cannot read rooms file: {e}")
            
            has_missing = any(missing_entries[key] for key in missing_entries)
            self.finished.emit({
                'valid': len(errors) == 0 and not has_missing,
                'errors': errors,
                'warnings': warnings,
                'files': self.files,
                'missing_entries': missing_entries
            })
            
        except Exception as e:
            self.finished.emit({
                'valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': [],
                'files': self.files
            })