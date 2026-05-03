"""
Core scheduling package
Handles greedy initialization, genetic algorithm optimization, and hybrid solving
"""

# Import main functions for easy access
from .assigner import (
    solve_schedule,
    SchedulerConfig,
    validate_assignment,
    generate_assignment_report,
    print_report
)

from .genetic_algorithm import (
    OptimizedChromosome,
    genetic_algorithm_optimized,
    adaptive_genetic_algorithm,
    mutate_swap_teachers_fast,
    crossover_uniform_fast,
    tournament_selection_fast
)

from .hybrid_solver import (
    solve_hybrid,
    HybridConfig,
    quick_solve,
    export_results
)

from .data_cleaner import (
    preprocess_exam_info,
    preprocess_professors
)

from .models import (
    Teacher,
    Session,
    teacher_from_dict,
    teacher_to_dict,
    session_from_dict,
    session_to_dict
)

from .calendar_parser import (
    CalendarParser
)

from .constraints import (
    has_duplicate_assignments,
    understaffed_deficit,
    capacity_excess,
    is_wish_violation,
    count_wish_violations
)

__all__ = [
    # Greedy
    'solve_schedule',
    'SchedulerConfig',
    'validate_assignment',
    'generate_assignment_report',
    'print_report',
    
    # GA
    'OptimizedChromosome',
    'genetic_algorithm_optimized',
    'adaptive_genetic_algorithm',
    
    # Hybrid
    'solve_hybrid',
    'HybridConfig',
    'quick_solve',
    'export_results',
    
    # Data processing
    'preprocess_exam_info',
    'preprocess_professors',
    'CalendarParser',

    # Models
    'Teacher',
    'Session',
    'teacher_from_dict',
    'teacher_to_dict',
    'session_from_dict',
    'session_to_dict',

    # Constraints
    'has_duplicate_assignments',
    'understaffed_deficit',
    'capacity_excess',
    'is_wish_violation',
    'count_wish_violations'
]

__version__ = '1.0.0'