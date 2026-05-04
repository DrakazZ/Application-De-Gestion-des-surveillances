import math
from collections import defaultdict
from dataclasses import dataclass, field

# ==================== CONFIGURATION ====================

@dataclass
class SchedulerConfig:
    """Centralized configuration for scheduler behavior"""
    min_per_room: int = 2
    padding_percentage: float = 0.10
    padding_caps: dict = field(default_factory=lambda: {
        5: 2, 25: 4, 40: 6, float('inf'): 7
    })
    default_max_sessions: int = 7
    hard_upper_cap: int = 20
    respect_wishes: bool = True
    prefer_responsible: bool = True
    balance_grades: bool = True
    use_lookahead: bool = True
    use_two_phase: bool = True
    time_mapping: dict = field(default_factory=lambda: {
        '08:30': 's1', '10:30': 's2', '12:30': 's3', '14:30': 's4'
    })


# ==================== INPUT VALIDATION ====================

def validate_inputs(df_calendar, df_profs, profs_by_session, rooms_by_session):
    """Validate inputs before processing"""
    errors = []
    
    if df_calendar.empty:
        errors.append("Calendar DataFrame is empty")
    
    if df_profs.empty:
        errors.append("Professors DataFrame is empty")
    
    # Check for required columns
    required_calendar_cols = ['Date', 'Time_Start']
    required_prof_cols = ['id', 'nom_complet', 'grade']
    
    for col in required_calendar_cols:
        if col not in df_calendar.columns:
            errors.append(f"Missing required calendar column: {col}")
    
    for col in required_prof_cols:
        if col not in df_profs.columns:
            errors.append(f"Missing required professor column: {col}")
    
    # Check for duplicate teacher IDs
    if df_profs['id'].duplicated().any():
        errors.append("Duplicate teacher IDs found")
    
    # Validate room counts are positive
    for key, rooms in rooms_by_session.items():
        if rooms <= 0:
            errors.append(f"Invalid room count for session {key}: {rooms}")
    
    if errors:
        raise ValueError("Input validation failed:\n" + "\n".join(errors))


# ==================== HELPER FUNCTIONS ====================

def normalize_time_str(t):
    """Convert '08h30' or '08:30' to '08:30'"""
    if isinstance(t, str) and 'h' in t:
        return t.replace('h', ':')
    return t


def session_key(date, time):
    """Generate unique session key"""
    return f"{date} {time}"


def pd_is_na(x):
    """Check if value is NaN (pandas-compatible)"""
    try:
        import pandas as pd
        return pd.isna(x)
    except Exception:
        return x is None


def time_to_seance_code(time_str, custom_mapping=None):
    """Flexible time to session code mapping"""
    if custom_mapping:
        return custom_mapping.get(time_str.strip(), 's?')
    
    # Parse time and auto-generate codes
    try:
        hour = int(time_str.split(':')[0])
        if 7 <= hour < 10:
            return 's1'
        elif 10 <= hour < 13:
            return 's2'
        elif 13 <= hour < 15:
            return 's3'
        elif 15 <= hour < 18:
            return 's4'
        else:
            return 's?'
    except:
        # Fallback to explicit mapping
        mapping = {'08:30': 's1', '10:30': 's2', '12:30': 's3', '14:30': 's4'}
        return mapping.get(time_str.strip(), 's?')


def parse_wishes_row(jour_str, seance_str):
    """Return dict {day_idx: [seance,...]} from aggregated strings"""
    if not jour_str or not seance_str:
        return {}
    days = [d.strip() for d in str(jour_str).split(',') if d.strip() != '']
    seances = [s.strip().lower() for s in str(seance_str).split(',') if s.strip() != '']
    d = {}
    for day, s in zip(days, seances):
        try:
            di = int(day)
        except Exception:
            continue
        d.setdefault(di, []).append(s)
    return d


def compute_padding(base_required, config: SchedulerConfig):
    """Compute padding = ceil(percentage%) clamped by caps"""
    p = math.ceil(config.padding_percentage * base_required)
    
    for threshold, cap in sorted(config.padding_caps.items()):
        if base_required <= threshold:
            return min(p, cap)
    
    return p

def find_transferable_session(donor, receiver, assignment, sessions, teachers, helpers):
    """
    Find a session that can be transferred from donor to receiver 
    without breaking any hard constraints.
    """
    donor_sessions = [s for s, assigned in assignment.items() if donor in assigned]
    for s in donor_sessions:
        session = sessions[s]
        # Check if receiver is available for this session
        if receiver not in assignment[s] and is_teacher_available(receiver, session, teachers, helpers):
            return s
    return None


def is_teacher_available(teacher_idx, session, teachers, helpers):
    """
    Checks if a teacher is available for a session (based on date/time/wishes).
    """
    teacher = teachers[teacher_idx]
    # You can extend this check depending on how wishes/availability are represented
    if session['date'] in teacher.get('unavailable_dates', []):
        return False
    if session['time'] in teacher.get('unavailable_times', []):
        return False
    return True


# ==================== ADAPTIVE CAPACITY PLANNING ====================

def compute_adaptive_grade_limits(
    teachers_by_grade,
    total_base_needed,
    user_limits=None,
    default_max=6,
    hard_upper_cap=20
):
    """
    Compute per-grade max_sessions so total capacity >= total_base_needed.
    
    Returns:
        adjusted_limits, adjustment_log
    """
    if user_limits is None:
        user_limits = {}

    # Initial limits
    limits = {}
    for grade, idxs in teachers_by_grade.items():
        limits[grade] = int(user_limits.get(grade, default_max))

    # Helper: compute current total capacity
    def capacity_from_limits(lims):
        return sum(len(teachers_by_grade[g]) * lim for g, lim in lims.items())

    cap = capacity_from_limits(limits)
    log = [{"action": "initial", "capacity": cap, "required": total_base_needed}]

    # If capacity is enough already
    if cap >= total_base_needed:
        log.append({"action": "ok", "capacity": cap, "required": total_base_needed})
        return limits, log

    # Otherwise try to adapt
    grades = list(limits.keys())
    iterations = 0
    max_iterations = 10000
    
    while cap < total_base_needed and iterations < max_iterations:
        grades.sort(key=lambda g: (limits[g], len(teachers_by_grade.get(g, []))))
        increased = False
        
        for g in grades:
            if limits[g] >= hard_upper_cap:
                continue
            limits[g] += 1
            added = len(teachers_by_grade.get(g, []))
            cap = capacity_from_limits(limits)
            log.append({
                "action": "increase",
                "grade": g,
                "new_limit": limits[g],
                "capacity_added": added,
                "total_capacity": cap
            })
            increased = True
            if cap >= total_base_needed:
                break
        
        if not increased:
            break
        iterations += 1

    # Final note if not possible
    if cap < total_base_needed:
        log.append({
            "action": "failed_to_cover",
            "capacity": cap,
            "required": total_base_needed,
            "note": "Reached hard upper caps; cannot cover demand automatically"
        })
    else:
        log.append({"action": "covered", "capacity": cap, "required": total_base_needed})

    return limits, log


# ==================== CANONICAL STRUCTURES ====================

def build_canonical_structures(
    df_calendar, 
    df_profs,
    profs_by_session, 
    rooms_by_session,
    config: SchedulerConfig = None,
    provided_ui_grade_limits=None
):
    """Build sessions, teachers, and helper structures"""
    
    if config is None:
        config = SchedulerConfig()
    
    # Validate inputs
    validate_inputs(df_calendar, df_profs, profs_by_session, rooms_by_session)
    
    # ========== Sessions ==========
    sessions = []
    session_idx_by_key = {}
    
    for i, row in df_calendar.iterrows():
        date = row['Date']
        tstart = normalize_time_str(row['Time_Start'])
        key = session_key(date, tstart)
        
        if key in session_idx_by_key:
            continue
        
        rooms = int(rooms_by_session.get(key, 1))
        base_required = rooms * config.min_per_room
        padding = compute_padding(base_required, config)
        total_required = base_required + padding
        
        sessions.append({
            "id": len(sessions),
            "key": key,
            "date": date,
            "time": tstart,
            "base_required_staff": base_required,
            "padding": padding,
            "total_required_staff": total_required,
            "responsible_teachers": profs_by_session.get(key, [])
        })
        session_idx_by_key[key] = sessions[-1]['id']

    # ========== Teachers ==========
    teachers = []
    teacher_index_by_id = {}
    
    for idx, row in df_profs.reset_index(drop=True).iterrows():
        tid = str(row.get('id', None))
        wishes = parse_wishes_row(row.get('jour', ''), row.get('seance', ''))
        submission_index = row.get('wish_submission_index', idx)
        
        teachers.append({
            "index": len(teachers),
            "id": tid,
            "name": row.get('nom_complet', ''),
            "grade": row.get('grade', ''),
            "max_sessions": int(row.get('max_sessions', config.default_max_sessions)),
            "assigned_sessions": set(),
            "total_sessions": 0,
            "wishes": wishes,
            "wish_submission_index": submission_index
        })
        teacher_index_by_id[tid] = len(teachers) - 1

    # ========== Group teachers by grade ==========
    teachers_by_grade = defaultdict(list)
    for t in teachers:
        teachers_by_grade[t['grade']].append(t['index'])

    # ========== Compute required totals ==========
    total_base_needed = sum(s['base_required_staff'] for s in sessions)

    # Preview before solving
    preview_capacity = sum(
        len(v) * config.default_max_sessions 
        for v in teachers_by_grade.values()
    )
    print(f"Total required staff: {total_base_needed}")
    print(f"Total current capacity (default={config.default_max_sessions}): {preview_capacity}")

    if provided_ui_grade_limits:
        print("UI limits:", provided_ui_grade_limits)

    # Compute adaptive limits
    adjusted_limits, adjustment_log = compute_adaptive_grade_limits(
        teachers_by_grade=teachers_by_grade,
        total_base_needed=total_base_needed,
        user_limits=provided_ui_grade_limits,
        default_max=config.default_max_sessions,
        hard_upper_cap=config.hard_upper_cap
    )

    # Apply adaptive limits per teacher
    for t in teachers:
        t["max_sessions"] = adjusted_limits.get(t["grade"], config.default_max_sessions)

    # ========== Helper structures ==========
    session_day_slot = {
        s['id']: (int(s['date'].split('/')[0]), time_to_seance_code(s['time'], config.time_mapping))
        for s in sessions
    }

    helpers = {
        'session_idx_by_key': session_idx_by_key,
        'teacher_index_by_id': teacher_index_by_id,
        'teachers_by_grade': teachers_by_grade,
        'session_day_slot': session_day_slot,
        'adjustment_log': adjustment_log,
        'adjusted_limits': adjusted_limits,
        'config': config
    }

    return sessions, teachers, helpers


# ==================== ASSIGNMENT LOGIC ====================

def is_available(teacher, session_id, helpers):
    """Check if teacher is available for session (no wish conflict)"""
    day_idx, seance = helpers['session_day_slot'][session_id]
    forbidden = teacher['wishes'].get(day_idx, [])
    return seance not in forbidden


def compute_session_difficulty(session, teachers, helpers):
    """Estimate how hard it will be to fill this session"""
    
    # Count available teachers for this session
    available_count = sum(
        1 for t in teachers 
        if t['total_sessions'] < t['max_sessions'] 
        and is_available(t, session['id'], helpers)
    )
    
    if available_count == 0:
        return float('inf')
    
    difficulty = session['total_required_staff'] / available_count
    
    # Bonus difficulty for sessions at unpopular times
    day_idx, seance = helpers['session_day_slot'][session['id']]
    unpopular_count = sum(
        1 for t in teachers 
        if seance in t['wishes'].get(day_idx, [])
    )
    difficulty *= (1 + unpopular_count / len(teachers))
    
    return difficulty


def build_candidate_pool(session_id, teachers, helpers, respect_wishes, already_assigned=None):
    """Build and categorize candidates efficiently"""
    
    if already_assigned is None:
        already_assigned = set()
    
    candidates = {
        'ideal': [],        # Available, under 80% capacity, matches wishes
        'good': [],         # Available, under max, matches wishes  
        'acceptable': [],   # Available, under max, violates wishes
        'emergency': []     # At max capacity but available
    }
    
    for t in teachers:
        # Skip if already assigned to this session
        if t['index'] in already_assigned:
            continue
            
        if t['max_sessions'] == 0:
            continue
            
        utilization = t['total_sessions'] / t['max_sessions']
        available = is_available(t, session_id, helpers)
        
        if utilization >= 1.0:
            if available:
                candidates['emergency'].append(t)
            continue
        
        if not available and respect_wishes:
            candidates['acceptable'].append(t)
            continue
        
        if utilization < 0.8:
            candidates['ideal'].append(t)
        else:
            candidates['good'].append(t)
    
    return candidates

def compute_fair_share(teachers, total_base_needed):
    """Compute fair share of sessions per teacher"""
    if not teachers:
        return 0
    return total_base_needed / len(teachers)

def enforce_equal_hours_per_grade(assignment, sessions, teachers, helpers):
    """
    Post-processing step that balances workload within each grade level
    """
    teachers_by_grade = helpers['teachers_by_grade']
    
    # Calculate current distribution
    for grade, teacher_indices in teachers_by_grade.items():
        grade_teachers = [teachers[idx] for idx in teacher_indices]
        total_sessions = sum(t['total_sessions'] for t in grade_teachers)
        target_per_teacher = total_sessions // len(grade_teachers)
        
        print(f"Grade {grade}: Target = {target_per_teacher} sessions per teacher")
        
        # Balance the assignments
        under_assigned = [t for t in grade_teachers if t['total_sessions'] < target_per_teacher]
        over_assigned = [t for t in grade_teachers if t['total_sessions'] > target_per_teacher]
        
        # Transfer sessions from over-assigned to under-assigned
        for receiver in under_assigned:
            while receiver['total_sessions'] < target_per_teacher and over_assigned:
                donor = over_assigned[0]
                
                # Find a session where donor is assigned but receiver isn't
                transfer_session = find_transferable_session(donor, receiver, assignment, sessions, teachers, helpers)

                
                if transfer_session:
                    # Transfer the assignment
                    assignment[transfer_session].remove(donor['index'])
                    assignment[transfer_session].append(receiver['index'])
                    
                    donor['total_sessions'] -= 1
                    receiver['total_sessions'] += 1
                    
                    if donor['total_sessions'] == target_per_teacher:
                        over_assigned.pop(0)
                else:
                    break

def rank_candidates(candidates, responsible_idxs, fair_share, balance_grades=False, helpers=None):
    """Rank candidates by priority using deterministic tie-breakers.

    Lower tuple sorts earlier (higher priority). Uses:
      1. responsible teacher (lowest)
      2. farthest below fair share (largest positive distance -> want them first)
      3. least utilized (lower utilization preferred)
      4. earlier wish submission index (lower -> submitted earlier -> higher priority)
    """
    def rank_key(t):
        is_responsible = 0 if t['index'] in responsible_idxs else 1
        distance_from_fair = fair_share - t['total_sessions']   # positive if below fair share
        utilization_rate = t['total_sessions'] / t['max_sessions'] if t['max_sessions'] > 0 else 1.0
        wish_idx = t.get('wish_submission_index', float('inf'))  # lower = earlier submission

        # Note: -distance_from_fair keeps those furthest below fair share first.
        return (
            is_responsible,
            -distance_from_fair,
            utilization_rate,
            wish_idx
        )

    return sorted(candidates, key=rank_key)



def balance_grade_distribution(candidates, needed, helpers):
    """Ensure diverse grade representation in selection"""
    
    if not candidates:
        return []
    
    # Group candidates by grade
    candidates_by_grade = defaultdict(list)
    for t in candidates:
        candidates_by_grade[t['grade']].append(t)
    
    # Calculate total teachers per grade
    total_teachers = sum(len(v) for v in helpers['teachers_by_grade'].values())
    
    # Target: proportional to teacher population
    grade_targets = {}
    for grade in candidates_by_grade.keys():
        proportion = len(helpers['teachers_by_grade'].get(grade, [])) / total_teachers
        grade_targets[grade] = max(1, int(needed * proportion))
    
    # Select candidates to match target distribution
    selected = []
    
    for grade in sorted(grade_targets.keys(), key=lambda g: grade_targets[g], reverse=True):
        target = grade_targets[grade]
        available = candidates_by_grade[grade]
        
        # Sort by workload within grade
        available.sort(key=lambda t: t['total_sessions'])
        
        for t in available[:target]:
            if len(selected) >= needed:
                break
            selected.append(t)
    
    # Fill remaining slots if needed
    remaining = needed - len(selected)
    if remaining > 0:
        all_remaining = [c for c in candidates if c not in selected]
        all_remaining.sort(key=lambda t: t['total_sessions'])
        selected.extend(all_remaining[:remaining])
    
    return selected[:needed]


def assign_to_session(
    session_id, 
    needed, 
    teachers, 
    helpers, 
    respect_wishes, 
    prefer_responsible,
    balance_grades=False,
    fair_share=None,
    already_assigned=None  # NEW: exclude already assigned teachers
):
    """Assign teachers to a single session with smart constraint relaxation"""
    
    if fair_share is None:
        fair_share = compute_fair_share(teachers, sum(t['total_sessions'] for t in teachers))
    
    if already_assigned is None:
        already_assigned = set()
    
    chosen = []
    violations = []
    
    # Get responsible teacher indices
    session = next(s for s in helpers.get('sessions', []) if s['id'] == session_id)
    responsible_idxs = []
    for rid in session.get('responsible_teachers', []):
        if rid is None:
            continue
        idx = helpers['teacher_index_by_id'].get(str(rid))
        if idx is not None:
            responsible_idxs.append(idx)
    
    # Build candidate pool (excluding already assigned)
    candidates = build_candidate_pool(session_id, teachers, helpers, respect_wishes, already_assigned)
    
    # Step 1: Try ideal candidates
    ideal = rank_candidates(candidates['ideal'], responsible_idxs, fair_share, balance_grades, helpers)
    if balance_grades:
        ideal = balance_grade_distribution(ideal, needed - len(chosen), helpers)
    chosen.extend([t['index'] for t in ideal[:needed - len(chosen)]])
    
    if len(chosen) >= needed:
        return chosen, violations
    
    # Step 2: Try good candidates
    good = rank_candidates(candidates['good'], responsible_idxs, fair_share, balance_grades, helpers)
    if balance_grades:
        good = balance_grade_distribution(good, needed - len(chosen), helpers)
    chosen.extend([t['index'] for t in good[:needed - len(chosen)]])
    
    if len(chosen) >= needed:
        return chosen, violations
    
    # Step 3: Violate wishes (minor violation)
    # rank acceptable candidates but prefer violating the *most recent* submitters first
    acceptable = rank_candidates(candidates['acceptable'], responsible_idxs, fair_share, balance_grades, helpers)

    # reverse ordering by wish_submission_index so later submitters are used first to violate
    acceptable_sorted_for_violation = sorted(
        acceptable,
        key=lambda t: t.get('wish_submission_index', float('inf')),
        reverse=True
    )

    for t in acceptable_sorted_for_violation:
        if len(chosen) >= needed:
            break
        # skip if already excluded by already_assigned (the build_candidate_pool already removed them, but double-check)
        if t['index'] in already_assigned:
            continue
        chosen.append(t['index'])
        violations.append({
            'session_id': session_id,
            'type': 'wish_violation',
            'teacher_index': t['index'],
            'teacher_id': t['id'],
            'severity': 'minor',
            'note': 'assigned despite wish conflict'
        })

    if len(chosen) >= needed:
        return chosen, violations
    
    # Step 4: Emergency - exceed max_sessions (major violation)
    emergency = rank_candidates(candidates['emergency'], responsible_idxs, fair_share, balance_grades, helpers)
    for t in emergency:
        if len(chosen) >= needed:
            break
        chosen.append(t['index'])
        violations.append({
            'session_id': session_id,
            'type': 'capacity_violation',
            'teacher_index': t['index'],
            'teacher_id': t['id'],
            'severity': 'major',
            'note': 'exceeded max_sessions capacity'
        })
    
    # Step 5: Still not enough (unsatisfiable)
    if len(chosen) < needed:
        violations.append({
            'session_id': session_id,
            'type': 'unsatisfiable',
            'needed': needed,
            'assigned': len(chosen),
            'severity': 'critical',
            'note': 'not enough available teachers even after all relaxations'
        })
    
    return chosen, violations


def greedy_assign(sessions, teachers, helpers, config: SchedulerConfig = None):
    """
    Greedy assignment with two-phase approach and smart constraint handling.
    
    Returns: assignment dict (session_id -> list of teacher_indices) and violation_log.
    """
    
    if config is None:
        config = helpers.get('config', SchedulerConfig())
    
    # Store sessions in helpers for access in subfunctions
    helpers['sessions'] = sessions
    
    # Convenience
    teacher_by_idx = {t['index']: t for t in teachers}
    assignment = {s['id']: [] for s in sessions}
    violation_log = []
    
    # Compute fair share
    total_base_needed = sum(s['base_required_staff'] for s in sessions)
    fair_share = compute_fair_share(teachers, total_base_needed)
    
    # Order sessions by difficulty if lookahead enabled
    if config.use_lookahead:
        session_order = sorted(
            sessions, 
            key=lambda s: compute_session_difficulty(s, teachers, helpers), 
            reverse=True
        )
    else:
        session_order = sorted(
            sessions, 
            key=lambda s: s['base_required_staff'], 
            reverse=True
        )
    
    # at start of greedy_assign (after assignment init)
    already_assigned_global = {s['id']: set() for s in sessions}

    # ========== PHASE 1: Fill base requirements ==========

    print("\nPhase 1: Filling base requirements...")

    for s in session_order:
        sid = s['id']
        needed = s['base_required_staff']

        chosen, violations = assign_to_session(
            sid, needed, teachers, helpers,
            config.respect_wishes, config.prefer_responsible,
            config.balance_grades, fair_share,
            already_assigned=already_assigned_global[sid]
        )


        # assign and update teacher state immediately
        assignment[sid].extend(chosen)
        for t_idx in chosen:
            already_assigned_global[sid].add(t_idx)
            t = teacher_by_idx[t_idx]
            t['assigned_sessions'].add(sid)
            t['total_sessions'] = len(t['assigned_sessions'])

        violation_log.extend(violations)

    # ========== PHASE 2: Distribute padding capacity ==========
    if config.use_two_phase:
        print("\nPhase 2: Distributing padding capacity...")
        
        # Recalculate fair share including padding
        total_with_padding = sum(s['total_required_staff'] for s in sessions)
        fair_share = compute_fair_share(teachers, total_with_padding)
        for s in session_order:
            sid = s['id']
            padding_slots = s['padding']
            if padding_slots == 0:
                continue

            additional, violations = assign_to_session(
                sid, padding_slots, teachers, helpers,
                config.respect_wishes, config.prefer_responsible,
                config.balance_grades, fair_share,
                already_assigned=already_assigned_global[sid]
            )

            additional = [t for t in additional if t not in already_assigned_global[sid]]

            assignment[sid].extend(additional)
            for t_idx in additional:
                already_assigned_global[sid].add(t_idx)
                t = teacher_by_idx[t_idx]
                t['assigned_sessions'].add(sid)
                t['total_sessions'] = len(t['assigned_sessions'])

            violation_log.extend(violations)

    # ========== PHASE 3: Balancing hours per grade ==========
    print("\nPhase 3: Balancing hours per grade...")
    enforce_equal_hours_per_grade(assignment, sessions, teachers, helpers)

    return assignment, violation_log


# ==================== REPORTING ====================

def validate_assignment(assignment, sessions, teachers):
    """Validate assignment for common errors"""
    errors = []
    warnings = []
    
    # Check for duplicate assignments within sessions
    for sid, teacher_indices in assignment.items():
        if len(teacher_indices) != len(set(teacher_indices)):
            duplicates = [t for t in teacher_indices if teacher_indices.count(t) > 1]
            errors.append(f"Session {sid} has duplicate teacher assignments: {duplicates}")
    
    # Check if teachers are assigned to sessions they shouldn't be
    teacher_by_idx = {t['index']: t for t in teachers}
    for sid, teacher_indices in assignment.items():
        for t_idx in teacher_indices:
            if t_idx not in teacher_by_idx:
                errors.append(f"Session {sid} assigned to non-existent teacher index {t_idx}")
    
    # Check teacher session counts match reality
    for t in teachers:
        actual_count = sum(1 for sid, indices in assignment.items() if t['index'] in indices)
        if actual_count != t['total_sessions']:
            warnings.append(
                f"Teacher {t['id']} has mismatched counts: "
                f"recorded={t['total_sessions']}, actual={actual_count}"
            )
    
    return errors, warnings


def generate_assignment_report(assignment, sessions, teachers, violations):
    """Generate detailed assignment statistics"""
    
    report = {
        'summary': {
            'total_sessions': len(sessions),
            'total_teachers': len(teachers),
            'total_assignments': sum(len(v) for v in assignment.values()),
            'total_violations': len(violations),
            'minor_violations': sum(1 for v in violations if v.get('severity') == 'minor'),
            'major_violations': sum(1 for v in violations if v.get('severity') == 'major'),
            'critical_violations': sum(1 for v in violations if v.get('severity') == 'critical')
        },
        'teacher_stats': [],
        'session_stats': [],
        'grade_distribution': {},
        'violation_summary': defaultdict(int)
    }
    
    # Per-teacher stats
    for t in teachers:
        utilization = t['total_sessions'] / t['max_sessions'] if t['max_sessions'] > 0 else 0
        report['teacher_stats'].append({
            'id': t['id'],
            'name': t['name'],
            'grade': t['grade'],
            'assigned': t['total_sessions'],
            'max': t['max_sessions'],
            'utilization': round(utilization, 2)
        })
    
    # Per-session stats
    for s in sessions:
        sid = s['id']
        assigned_count = len(assignment[sid])
        report['session_stats'].append({
            'session': s['key'],
            'required': s['total_required_staff'],
            'base_required': s['base_required_staff'],
            'padding': s['padding'],
            'assigned': assigned_count,
            'deficit': max(0, s['total_required_staff'] - assigned_count),
            'surplus': max(0, assigned_count - s['total_required_staff'])
        })
    
    # Grade distribution
    for grade in set(t['grade'] for t in teachers):
        grade_teachers = [t for t in teachers if t['grade'] == grade]
        total_assigned = sum(t['total_sessions'] for t in grade_teachers)
        avg = total_assigned / len(grade_teachers) if grade_teachers else 0
        report['grade_distribution'][grade] = {
            'teachers': len(grade_teachers),
            'total_sessions': total_assigned,
            'avg_per_teacher': round(avg, 2)
        }
    
    # Violation summary
    for v in violations:
        vtype = v.get('type', 'unknown')
        report['violation_summary'][vtype] += 1
    
    return report


def print_report(report):
    """Pretty print the assignment report"""
    
    print("\n" + "="*60)
    print("ASSIGNMENT REPORT")
    print("="*60)
    
    print("\nSUMMARY:")
    for key, value in report['summary'].items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    
    print("\nGRADE DISTRIBUTION:")
    for grade, stats in sorted(report['grade_distribution'].items()):
        print(f"  {grade}:")
        print(f"    Teachers: {stats['teachers']}")
        print(f"    Total Sessions: {stats['total_sessions']}")
        print(f"    Avg per Teacher: {stats['avg_per_teacher']}")
    
    print("\nVIOLATION SUMMARY:")
    if report['violation_summary']:
        for vtype, count in sorted(report['violation_summary'].items()):
            print(f"  {vtype.replace('_', ' ').title()}: {count}")
    else:
        print("  No violations!")
    
    print("\nTEACHER WORKLOAD (Top 10 Most Utilized):")
    sorted_teachers = sorted(
        report['teacher_stats'], 
        key=lambda x: x['utilization'], 
        reverse=True
    )[:10]
    for t in sorted_teachers:
        print(f"  {t['name']} ({t['grade']}): {t['assigned']}/{t['max']} ({t['utilization']*100:.0f}%)")
    
    print("\nSESSION COVERAGE (Sessions with Deficits):")
    deficit_sessions = [s for s in report['session_stats'] if s['deficit'] > 0]
    if deficit_sessions:
        for s in deficit_sessions[:10]:
            print(f"  {s['session']}: {s['assigned']}/{s['required']} (deficit: {s['deficit']})")
    else:
        print("  All sessions fully covered!")
    
    print("\n" + "="*60)


# ==================== MAIN ENTRY POINT ====================

def solve_schedule(
    df_calendar,
    df_profs,
    profs_by_session,
    rooms_by_session,
    config: SchedulerConfig = None,
    provided_ui_grade_limits=None
):
    """
    Main entry point for scheduling algorithm.
    
    Returns:
        assignment: dict mapping session_id to list of teacher indices
        sessions: list of session objects
        teachers: list of teacher objects
        report: detailed statistics report
    """
    
    if config is None:
        config = SchedulerConfig()
    
    print("Building canonical structures...")
    sessions, teachers, helpers = build_canonical_structures(
        df_calendar, df_profs, profs_by_session, rooms_by_session,
        config, provided_ui_grade_limits
    )
    
    print("\nRunning greedy assignment algorithm...")
    assignment, violations = greedy_assign(sessions, teachers, helpers, config)
    
    print("\nValidating assignment...")
    errors, warnings = validate_assignment(assignment, sessions, teachers)
    
    if errors:
        print("\nWARNING: VALIDATION ERRORS FOUND:")
        for error in errors:
            print(f"  ERROR: {error}")
        raise ValueError("Assignment validation failed. See errors above.")
    
    if warnings:
        print("\nWARNING: VALIDATION WARNINGS:")
        for warning in warnings:
            print(f"  WARNING: {warning}")
    
    print("\nGenerating report...")
    report = generate_assignment_report(assignment, sessions, teachers, violations)
    
    print_report(report)
    
    return assignment, sessions, teachers, report, violations, helpers