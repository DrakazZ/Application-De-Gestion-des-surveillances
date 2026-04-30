import json
from assigner import solve_schedule  

def run_scheduler_for_ui(df_calendar, df_profs, profs_by_session, rooms_by_session,
                         ui_grade_limits=None, config=None):
    """
    Wrapper that runs the scheduler and returns JSON-serializable results for the UI.

    Returns dict with keys:
      - 'assignment' : { session_key: [teacher_ids...] }
      - 'sessions' : list of session dicts (key, required, base, padding)
      - 'teachers' : list of teacher summaries (id, name, grade, assigned)
      - 'report' : the summary report dict (from generate_assignment_report)
      - 'adjustment_log' : list of adjustments made to grade limits
      - 'violations' : list of violation dicts
    """
    assignment, sessions, teachers, report, violations, helpers = solve_schedule(
        df_calendar, df_profs, profs_by_session, rooms_by_session,
        config=config, provided_ui_grade_limits=ui_grade_limits
    )

    # convert assignment indices -> teacher ids, and session id -> session key
    session_map = {s['id']: s['key'] for s in sessions}
    teacher_map = {t['index']: t['id'] for t in teachers}

    assignment_by_key = {}
    for sid, t_indices in assignment.items():
        assignment_by_key[session_map[sid]] = [teacher_map.get(i) for i in t_indices]

    # build teachers summary
    teacher_summaries = [{
        'id': t['id'],
        'name': t['name'],
        'grade': t['grade'],
        'assigned': t['total_sessions'],
        'max_sessions': t['max_sessions']
    } for t in teachers]

    return {
        'assignment': assignment_by_key,
        'sessions': sessions,
        'teachers': teacher_summaries,
        'report': report,
        'adjustment_log': helpers,  
        'violations': violations
    }

