Perfect question. Here is the full end-to-end mapping of how data flows right now, with concrete formats and where logic gets inconsistent.

**1) Entry point and execution chain (as implemented now)**
1. User selects files in DataInputPanel and clicks Importer.
- Signal emitted: data_input_panel.py
- Connected in HomePage: home_page.py, home_page.py

2. HomePage validates files and settings, then starts ValidationWorker.
- Validation entry: home_page.py
- Worker creation/start: home_page.py, home_page.py

3. If validation passes, HomePage starts SchedulerWorker.
- Handoff: home_page.py, home_page.py, home_page.py

4. SchedulerWorker executes the full hybrid pipeline.
- Pipeline method: backend_worker.py
- Steps called in order:
  - Calendar parsing: backend_worker.py, backend_worker.py
  - Exam-room preprocessing: backend_worker.py
  - Professor preprocessing: backend_worker.py
  - Hybrid solve: backend_worker.py

5. Result comes back to HomePage, transformed for export panel.
- UI completion handler: home_page.py
- Build flat assignment table for export: home_page.py
- Export panel receives in-memory result: export_panel.py

---

**2) Raw input data and expected format**

1. Calendar PDF
- Used by CalendarParser: calendar_parser.py
- YOLO detections from model: inference.py

2. Rooms assignment Excel (salles)
- Preprocessed by: data_cleaner.py
- Required columns checked in validation:
  - enseignant
  - dateExam
  - h_debut
  - h_fin
- Check location: backend_worker.py

3. Professors Excel (professeurs)
- Preprocessed by: data_cleaner.py
- Required in validation:
  - nom_ens
  - prenom_ens
  - grade_code_ens
- Check location: backend_worker.py

4. Wishes Excel (souhaits)
- Preprocessed together with professors: data_cleaner.py
- Required columns in validation:
  - enseignant_uuid.nom_ens
  - enseignant_uuid.prenom_ens
  - jour
  - seance
- Check location: backend_worker.py

Small example of raw intent:
- salles row:
  - enseignant = 1023
  - dateExam = 14/05/2026
  - h_debut = 08:30
  - h_fin = 10:00
- professeurs row:
  - code_smartex_ens = 1023
  - nom_ens = Ben Ali
  - prenom_ens = Salma
  - grade_code_ens = MA
  - participe_surveillance = true
- souhaits row:
  - enseignant_uuid.nom_ens = Ben Ali
  - enseignant_uuid.prenom_ens = Salma
  - jour = 14
  - seance = s1

---

**3) Calendar PDF to structured sessions**

1. PDF pages are converted to images.
- calendar_parser.py

2. YOLO detects rows and cells, labels loaded from txt files.
- calendar_parser.py

3. For each page:
- grid built from detected rows/cells: calendar_parser.py
- date rows detected and nearest date row used to label exam cells: calendar_parser.py, calendar_parser.py

4. Output of parser is DataFrame df_calendar.
- Returned from: calendar_parser.py
- Typical columns:
  - Date (DD/MM)
  - Time_Start (08h30 style from parser)
  - Time_End
  - Subject
  - Class

Small example df_calendar rows:
- Date=14/05, Time_Start=08h30, Subject=Algo, Class=L2
- Date=14/05, Time_Start=10h30, Subject=DB, Class=L2

---

**4) Non-PDF preprocessing outputs**

1. preprocess_exam_info output
- Function: data_cleaner.py
- Returns:
  - profs_by_session: dict mapping "DD/MM HH:MM" -> set of responsible teacher IDs
  - rooms_by_session: dict mapping "DD/MM HH:MM" -> number of room rows

Example:
- profs_by_session["14/05 08:30"] = {"1023", "1178"}
- rooms_by_session["14/05 08:30"] = 3

2. preprocess_professors output
- Function: data_cleaner.py
- Returns df_profs with:
  - id
  - nom_complet
  - grade
  - jour (aggregated comma string)
  - seance (aggregated comma string)

Example row:
- id=1023
- nom_complet=Ben Ali Salma
- grade=MA
- jour=14,16
- seance=s1,s2

---

**5) Hybrid solver phase 1: canonicalization + greedy**

1. Entry into hybrid solve
- hybrid_solver.py

2. Greedy starts by calling solve_schedule
- hybrid_solver.py
- solve_schedule in: assigner.py

3. build_canonical_structures creates internal structures
- assigner.py

It creates:

a) sessions list
- Each element:
  - id
  - key (Date + normalized Time_Start)
  - date
  - time
  - base_required_staff = rooms * min_per_room
  - padding
  - total_required_staff
  - responsible_teachers
- Time normalization happens here (08h30 -> 08:30): assigner.py, assigner.py

b) teachers list
- Each element:
  - index
  - id as string
  - name
  - grade
  - max_sessions
  - assigned_sessions set
  - total_sessions
  - wishes parsed to dict day -> list of seance
  - wish_submission_index
- parse_wishes_row: assigner.py

c) helpers dict
- teacher/session indices and mappings:
  - teacher_index_by_id
  - session_idx_by_key
  - teachers_by_grade
  - session_day_slot
  - adjusted_limits

4. Adaptive grade limits are computed before assignment
- assigner.py

5. Greedy assignment execution
- Main greedy: assigner.py

Execution phases:
1. Order sessions by difficulty.
2. Phase 1 fills base_required_staff.
3. Phase 2 fills padding.
4. Phase 3 tries balancing per grade.

Core assignment function:
- assigner.py

Candidate pools:
- ideal, good, acceptable, emergency
- assigner.py

Small greedy example:
- Session 14/05 08:30 has 3 rooms
- min_per_room=2 -> base_required=6
- padding maybe 1 -> total_required=7
- Greedy first assigns 6, then maybe +1 in phase 2

---

**6) Handoff to GA phase**

1. Greedy output is wrapped into OptimizedChromosome
- hybrid_solver.py

2. GA starts with greedy assignment as seed
- hybrid_solver.py
- GA function: genetic_algorithm.py

3. Population initialization
- First individual = greedy
- Others = mutated copies
- genetic_algorithm.py

4. Evolution loop
- Elitism
- Tournament selection
- Uniform crossover
- Swap mutation
- Fitness evaluation
- genetic_algorithm.py

---

**7) GA fitness data usage and current inconsistency**

1. Fitness is computed here:
- genetic_algorithm.py

2. Data used:
- genes: dict session_id -> list of teacher indices
- sessions metadata
- teachers metadata
- helpers session_day_slot

3. Main issue (critical inconsistency):
- Understaffing uses:
  - required = session total_required_staff
  - assigned = len(session responsible_teachers)
- Instead of assigned = len(genes[sid])
- Lines: genetic_algorithm.py, genetic_algorithm.py

Why this is wrong:
- responsible_teachers comes from rooms file responsible IDs, not final assigned staff count.
- So GA can improve score while real staffing in genes is bad, or get penalized despite enough assignments.

Small example:
- Suppose session requires 6.
- genes[sid] has 6 assigned teachers.
- responsible_teachers length is 1.
- Fitness computes deficit 5 and penalizes anyway.
- This directly breaks objective consistency between greedy output quality and GA scoring.

4. Additional inconsistency in same block:
- It repeats understaffed penalty per assigned teacher based on same wrong assigned value.
- genetic_algorithm.py

---

**8) More logic inconsistencies affecting understanding/results**

1. Wishes file handling mismatch
- Validation may allow missing wishes as warning: backend_worker.py
- But preprocessing always reads wishes file: data_cleaner.py
- Can fail after user proceeds.

2. Duplicate signal connection
- import_requested connected twice: home_page.py, home_page.py
- Can trigger duplicate executions.

3. Grade balancing transfer likely non-functional
- Balancer passes donor/receiver teacher dicts where helper expects indices in assignment lists.
- Call site: assigner.py
- Check logic in helper: assigner.py
- Result: transfer often never happens.

4. Parser control flow is fragile
- date_columns rebuilt in multiple loops and reused outside loop scope.
- calendar_parser.py, calendar_parser.py, calendar_parser.py

---

**9) Final output format (current behavior)**

1. SchedulerWorker returns dictionary:
- result: full hybrid output
- stats: UI stats summary
- backend_worker.py

2. hybrid result includes:
- final_assignment
- final_chromosome
- greedy_chromosome
- sessions
- teachers
- helpers
- comparison
- ga_history
- timing and mode
- hybrid_solver.py

3. HomePage builds exportable flat DataFrame final_df:
- columns:
  - Date
  - Time
  - Teacher
- home_page.py

Example final_df rows:
- Date=14/05, Time=08:30, Teacher=Ben Ali Salma
- Date=14/05, Time=08:30, Teacher=Trabelsi Nader
- Date=14/05, Time=10:30, Teacher=Haddad Rym

4. Export layer uses this final_df for Excel and Word.
- home_page.py, home_page.py, export_docs.py

