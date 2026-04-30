"""
Hybrid Solver: Combines Greedy Initialization with Genetic Algorithm Optimization
"""

import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# Import your modules
from .assigner import (
    solve_schedule,
    validate_assignment,
    SchedulerConfig,
    generate_assignment_report
)

from .genetic_algorithm import (
    OptimizedChromosome,
    genetic_algorithm_optimized,
    compare_solutions
)


@dataclass
class HybridConfig:
    """Configuration for the hybrid solver"""
    # Greedy configuration
    greedy_config: SchedulerConfig = None
    
    # GA parameters
    population_size: int = 50
    generations: int = 500
    crossover_rate: float = 0.8
    mutation_rate: float = 0.15
    elitism_count: int = 5
    tournament_size: int = 3
    
    # Execution
    verbose: bool = True
    use_ga: bool = True  # Set False to run greedy only


def solve_hybrid(
    df_calendar,
    df_profs,
    profs_by_session,
    rooms_by_session,
    config: HybridConfig = None,
    provided_ui_grade_limits=None,
    progress_callback=None
) -> Dict:
    """
    Main hybrid solver: Greedy initialization + GA optimization.
    
    Args:
        df_calendar: Calendar DataFrame with sessions
        df_profs: Professors DataFrame  
        profs_by_session: Dict mapping session keys to responsible professors
        rooms_by_session: Dict mapping session keys to room counts
        config: Hybrid configuration
        provided_ui_grade_limits: User-specified grade limits
        progress_callback: Function(stage, progress_dict) for UI updates
    
    Returns:
        Dict with complete results:
        {
            'final_assignment': best assignment dict,
            'final_chromosome': best ScheduleChromosome,
            'greedy_chromosome': initial greedy solution,
            'sessions': session list,
            'teachers': teacher list,
            'helpers': helper structures,
            'comparison': comparison statistics,
            'ga_history': evolution history,
            'execution_time': total time in seconds
        }
    """
    
    if config is None:
        config = HybridConfig()
    
    if config.greedy_config is None:
        config.greedy_config = SchedulerConfig()
    
    start_time = time.time()
    
    print("\n" + "="*70)
    print(" "*20 + "HYBRID SCHEDULER")
    print("="*70)
    print(f"Mode: {'Greedy + Genetic Algorithm' if config.use_ga else 'Greedy Only'}")
    print("="*70)
    
    # ========== PHASE 1: GREEDY INITIALIZATION ==========
    
    if progress_callback:
        progress_callback('greedy', {'stage': 'starting', 'progress': 0})
    
    print("\n📊 PHASE 1: GREEDY INITIALIZATION")
    print("-" * 70)
    
    greedy_start = time.time()
    
    # Run greedy algorithm
    (greedy_assignment, sessions, teachers, greedy_report, 
     greedy_violations, helpers) = solve_schedule(
        df_calendar, df_profs, profs_by_session, rooms_by_session,
        config.greedy_config, provided_ui_grade_limits
    )
    
    greedy_time = time.time() - greedy_start
    
    # Wrap in chromosome for consistent interface
    greedy_chromosome = OptimizedChromosome(
        greedy_assignment, sessions, teachers, helpers
    )

    print("=== GENE REFERENCE CHECK ===")
    print("Same object:", id(greedy_assignment) == id(greedy_chromosome.genes))
    print("Assignment type:", type(greedy_assignment))
    print("Genes type:", type(greedy_chromosome.genes))
    sample_sid = next(iter(greedy_assignment.keys()))
    print("Sample assignment:", greedy_assignment[sample_sid])
    print("Sample genes:", greedy_chromosome.genes[sample_sid])
    
    print(f"\n✓ Greedy phase completed in {greedy_time:.2f}s")
    print(f"  Initial fitness: {greedy_chromosome.fitness_score:.2f}")
    print(f"  Initial violations: {len(greedy_chromosome.violations)}")
    
    if progress_callback:
        progress_callback('greedy', {
            'stage': 'complete',
            'progress': 100,
            'time': greedy_time,
            'fitness': greedy_chromosome.fitness_score,
            'violations': len(greedy_chromosome.violations)
        })
    
    # If GA disabled, return greedy solution
    if not config.use_ga:
        total_time = time.time() - start_time
        print(f"\n✓ Total execution time: {total_time:.2f}s")
        
        return {
            'final_assignment': greedy_assignment,
            'final_chromosome': greedy_chromosome,
            'greedy_chromosome': greedy_chromosome,
            'sessions': sessions,
            'teachers': teachers,
            'helpers': helpers,
            'comparison': None,
            'ga_history': None,
            'execution_time': total_time,
            'mode': 'greedy_only'
        }
    
    # ========== PHASE 2: GENETIC ALGORITHM OPTIMIZATION ==========
    
    if progress_callback:
        progress_callback('ga', {'stage': 'starting', 'progress': 0, 'generation': 0})
    
    print("\n🧬 PHASE 2: GENETIC ALGORITHM OPTIMIZATION")
    print("-" * 70)
    
    ga_start = time.time()
    
    # GA callback for progress updates
    def ga_callback(gen_stats):
        if progress_callback:
            progress = (gen_stats['generation'] / config.generations) * 100
            progress_callback('ga', {
                'stage': 'running',
                'progress': progress,
                'generation': gen_stats['generation'],
                'best_fitness': gen_stats['best_fitness'],
                'avg_fitness': gen_stats['avg_fitness'],
                'violations': gen_stats['best_violations']
            })
    
    # Run genetic algorithm
    best_chromosome, ga_history = genetic_algorithm_optimized(
        initial_solution=greedy_assignment,
        sessions=sessions,
        teachers=teachers,
        helpers=helpers,
        population_size=config.population_size,
        generations=config.generations,
        crossover_rate=config.crossover_rate,
        mutation_rate=config.mutation_rate,
        elitism_count=config.elitism_count,
        tournament_size=config.tournament_size,
        verbose=config.verbose,
        callback=ga_callback
    )
    
    ga_time = time.time() - ga_start
    
    if progress_callback:
        progress_callback('ga', {
            'stage': 'complete',
            'progress': 100,
            'time': ga_time
        })
    
    # ========== PHASE 3: COMPARISON & VALIDATION ==========
    
    print("\n📈 PHASE 3: RESULTS COMPARISON")
    print("-" * 70)
    
    comparison = compare_solutions(greedy_chromosome, best_chromosome)
    
    # Print comparison table
    print("\n{:<25} {:>15} {:>15} {:>12}".format(
        "Metric", "Greedy", "GA", "Improvement"
    ))
    print("-" * 70)
    for i in range(len(comparison['metric'])):
        print("{:<25} {:>15} {:>15} {:>12}".format(
            comparison['metric'][i],
            str(comparison['greedy'][i])[:15],
            str(comparison['genetic_algorithm'][i])[:15],
            comparison['improvement'][i]
        ))
    
    # Validate final solution
    print("\n🔍 Validating final solution...")
    errors, warnings = validate_assignment(best_chromosome.genes, sessions, teachers)
    
    if errors:
        print("⚠️  ERRORS FOUND:")
        for error in errors:
            print(f"  ❌ {error}")
    else:
        print("✓ No errors found")
    
    if warnings:
        print("⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  ⚠️  {warning}")
    
    # ========== FINAL SUMMARY ==========
    
    total_time = time.time() - start_time
    
    print("\n" + "="*70)
    print(" "*25 + "FINAL SUMMARY")
    print("="*70)
    print(f"Greedy time:     {greedy_time:>6.2f}s")
    print(f"GA time:         {ga_time:>6.2f}s")
    print(f"Total time:      {total_time:>6.2f}s")
    print(f"\nInitial fitness: {greedy_chromosome.fitness_score:>8.2f}")
    print(f"Final fitness:   {best_chromosome.fitness_score:>8.2f}")
    improvement_pct = ((best_chromosome.fitness_score - greedy_chromosome.fitness_score) / 
                       abs(greedy_chromosome.fitness_score) * 100)
    print(f"Improvement:     {improvement_pct:>7.2f}%")
    print("="*70 + "\n")
    
    return {
        'final_assignment': best_chromosome.genes,
        'final_chromosome': best_chromosome,
        'greedy_chromosome': greedy_chromosome,
        'sessions': sessions,
        'teachers': teachers,
        'helpers': helpers,
        'comparison': comparison,
        'ga_history': ga_history,
        'execution_time': total_time,
        'greedy_time': greedy_time,
        'ga_time': ga_time,
        'mode': 'hybrid'
    }


# ==================== CONVENIENCE FUNCTIONS ====================

def quick_solve(df_calendar, df_profs, profs_by_session, rooms_by_session,
                use_ga=True, generations=100):
    """
    Quick solve with default settings.
    
    Args:
        use_ga: Whether to use genetic algorithm (True) or greedy only (False)
        generations: Number of GA generations if use_ga=True
    """
    config = HybridConfig(
        use_ga=use_ga,
        generations=generations,
        verbose=True
    )
    
    return solve_hybrid(
        df_calendar, df_profs, profs_by_session, rooms_by_session,
        config=config
    )


def export_results(result: Dict, output_prefix: str = "schedule"):
    """
    Export results to files.
    
    Generates:
    - {prefix}_assignment.xlsx: Final schedule
    - {prefix}_comparison.csv: Greedy vs GA comparison
    - {prefix}_report.txt: Detailed text report
    """
    import pandas as pd
    
    # 1. Export final assignment
    rows = []
    for s in result['sessions']:
        sid = s['id']
        teachers_assigned = [
            result['teachers'][t_idx]['name'] 
            for t_idx in result['final_assignment'][sid]
        ]
        rows.append({
            'Date': s['date'],
            'Time': s['time'],
            'Required Staff': s['total_required_staff'],
            'Assigned Staff': len(result['final_assignment'][sid]),
            'Teachers': ', '.join(teachers_assigned),
            'Status': 'OK' if len(result['final_assignment'][sid]) >= s['total_required_staff'] else 'UNDERSTAFFED'
        })
    
    df = pd.DataFrame(rows)
    df.to_excel(f'{output_prefix}_assignment.xlsx', index=False)
    print(f"✓ Exported assignment to {output_prefix}_assignment.xlsx")
    
    # 2. Export comparison if GA was used
    if result['comparison']:
        comp_df = pd.DataFrame(result['comparison'])
        comp_df.to_csv(f'{output_prefix}_comparison.csv', index=False)
        print(f"✓ Exported comparison to {output_prefix}_comparison.csv")
    
    # 3. Export detailed report
    with open(f'{output_prefix}_report.txt', 'w') as f:
        f.write("="*70 + "\n")
        f.write(" "*20 + "SCHEDULING REPORT\n")
        f.write("="*70 + "\n\n")
        
        f.write(f"Mode: {result['mode']}\n")
        f.write(f"Total execution time: {result['execution_time']:.2f}s\n\n")
        
        if result['mode'] == 'hybrid':
            f.write(f"Greedy time: {result['greedy_time']:.2f}s\n")
            f.write(f"GA time: {result['ga_time']:.2f}s\n\n")
        
        f.write(f"Total sessions: {len(result['sessions'])}\n")
        f.write(f"Total teachers: {len(result['teachers'])}\n")
        f.write(f"Total assignments: {sum(len(v) for v in result['final_assignment'].values())}\n\n")
        
        f.write("Final Solution:\n")
        f.write(f"  Fitness: {result['final_chromosome'].fitness_score:.2f}\n")
        f.write(f"  Violations: {len(result['final_chromosome'].violations)}\n")
        f.write(f"  Wish violations: {result['final_chromosome'].stats['wish_violations']}\n")
        f.write(f"  Workload variance: {result['final_chromosome'].stats['workload_variance']:.2f}\n")
    
    print(f"✓ Exported report to {output_prefix}_report.txt")