"""
Shared constraint checks for greedy and GA.
"""

from typing import Dict, Iterable, List, Tuple


def has_duplicate_assignments(teacher_indices: Iterable[int]) -> bool:
    """Return True if a session assignment contains duplicates."""
    teacher_list = list(teacher_indices)
    return len(teacher_list) != len(set(teacher_list))


def understaffed_deficit(required_staff: int, assigned_count: int) -> int:
    """Return positive deficit if assigned < required."""
    return max(0, required_staff - assigned_count)


def capacity_excess(teacher_counts, max_sessions) -> int:
    """Return total assignments above max_sessions across teachers."""
    return int(sum(max(c - m, 0) for c, m in zip(teacher_counts, max_sessions)))


def is_wish_violation(teacher: Dict, day_idx: int, seance: str) -> bool:
    """Return True if the session violates the teacher's wishes."""
    forbidden = teacher.get("wishes", {}).get(day_idx, [])
    return seance in forbidden


def count_wish_violations(
    genes: Dict[int, List[int]],
    teachers: List[Dict],
    session_day_slot: Dict[int, Tuple[int, str]]
) -> int:
    """Count wish violations across all assignments."""
    violations = 0
    for sid, teacher_indices in genes.items():
        day_idx, seance = session_day_slot[sid]
        for t_idx in teacher_indices:
            if is_wish_violation(teachers[t_idx], day_idx, seance):
                violations += 1
    return violations


__all__ = [
    "has_duplicate_assignments",
    "understaffed_deficit",
    "capacity_excess",
    "is_wish_violation",
    "count_wish_violations",
]
