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
    mutate_swap_teachers_fast,
    crossover_uniform_fast,
    tournament_selection_fast
)

from .hybrid_solver import (
    solve_hybrid,
    HybridConfig,
)

from .data_cleaner import (
    preprocess_exam_info,
    preprocess_professors
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
    
    # Hybrid
    'solve_hybrid',
    'HybridConfig',
    
    # Data processing
    'preprocess_exam_info',
    'preprocess_professors',
    
]

__version__ = '1.0.0'