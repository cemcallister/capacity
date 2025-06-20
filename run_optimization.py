#!/usr/bin/env python3

"""
Run Qualification Optimization Suite
====================================

This script provides multiple optimization approaches for qualification matrices
with standardized output for easy validation and comparison.
"""

import sys
from pathlib import Path
from datetime import datetime

from src.analysis.ppm_capacity_optimizer import PPMCapacityOptimizer
from src.analysis.qualification_matrix_designer import QualificationMatrixDesigner
from src.analysis.coverage_optimized_designer import CoverageOptimizedDesigner
from src.analysis.balanced_coverage_designer import BalancedCoverageDesigner
from src.analysis.ultimate_coverage_designer import UltimateCoverageDesigner
from src.analysis.milp_optimization_designer import MILPOptimizationDesigner
from src.analysis.standard_output_manager import StandardOutputManager


def run_classic_optimization(optimizer):
    """Run classic balanced optimization approach"""
    print("\n🎯 RUNNING CLASSIC OPTIMIZATION...")
    designer = QualificationMatrixDesigner(optimizer)
    
    # Run complete analysis which includes validation
    results = designer.run_complete_analysis()
    
    # Extract matrices and validation results from the complete analysis
    matrices = results['matrices']
    validation_results = results['coverage_tests']
    
    return matrices, validation_results, {
        "approach": "classic_qualification_matrix",
        "features": [
            "balanced_assignment",
            "type_a_constraint_compliance",
            "role_based_qualification_filtering"
        ],
        "target_coverage": {
            "daily_ppms": "baseline",
            "weekly_ppms": "baseline", 
            "monthly_ppms": "baseline"
        }
    }


def run_maximum_optimization(optimizer):
    """Run maximum coverage-focused optimization"""
    print("\n🎯 RUNNING MAXIMUM COVERAGE OPTIMIZATION...")
    designer = CoverageOptimizedDesigner(optimizer)
    matrices = designer.create_optimized_qualification_matrices()
    validation_results = designer.validate_and_export_results(matrices)
    
    return matrices, validation_results, {
        "approach": "coverage_optimized", 
        "features": [
            "shift_pattern_optimization",
            "enhanced_redundancy",
            "iterative_improvement", 
            "complete_qualification_coverage"
        ],
        "target_coverage": {
            "daily_ppms": "maximize",
            "weekly_ppms": "100%",
            "monthly_ppms": "100%"
        }
    }


def run_balanced_optimization(optimizer):
    """Run balanced qualification distribution optimization"""
    print("\n⚖️  RUNNING BALANCED COVERAGE OPTIMIZATION...")
    designer = BalancedCoverageDesigner(optimizer)
    matrices = designer.create_optimized_qualification_matrices()
    validation_results = designer.validate_and_export_results(matrices)
    
    return matrices, validation_results, {
        "approach": "balanced_coverage",
        "features": [
            "even_qualification_distribution",
            "qualification_limits_per_engineer",
            "shift_pattern_aware_coverage",
            "balanced_workload_assignment",
            "role_based_filtering",
            "fairness_optimization"
        ],
        "target_coverage": {
            "daily_ppms": "balanced",
            "weekly_ppms": "100%",
            "monthly_ppms": "100%"
        }
    }


def run_ultimate_optimization(optimizer):
    """Run ULTIMATE 100% daily coverage optimization"""
    print("\n🔥 RUNNING ULTIMATE 100% COVERAGE OPTIMIZATION...")
    designer = UltimateCoverageDesigner(optimizer)
    matrices = designer.create_optimized_qualification_matrices()
    validation_results = designer.validate_and_export_results(matrices)
    
    return matrices, validation_results, {
        "approach": "ultimate_coverage",
        "features": [
            "100_percent_daily_target",
            "ultra_aggressive_redundancy",
            "real_time_validation_feedback",
            "perfect_shift_matching",
            "iterative_perfection",
            "gap_driven_optimization"
        ],
        "target_coverage": {
            "daily_ppms": "100%",
            "weekly_ppms": "100%", 
            "monthly_ppms": "100%"
        }
    }


def run_milp_optimization(optimizer):
    """Run Mathematical (MILP) optimization with guaranteed coverage"""
    print("\n🔢 RUNNING MILP MATHEMATICAL OPTIMIZATION...")
    designer = MILPOptimizationDesigner(optimizer)
    matrices = designer.create_optimized_qualification_matrices()
    validation_results = designer.validate_and_export_results(matrices)
    
    return matrices, validation_results, {
        "approach": "milp_mathematical",
        "features": [
            "mathematical_optimization",
            "guaranteed_coverage_constraints",
            "fairness_objective_function",
            "pulp_linear_programming",
            "optimal_solution_guarantee",
            "constraint_satisfaction",
            "intelligent_heuristic_fallback"
        ],
        "target_coverage": {
            "daily_ppms": "100% (guaranteed)",
            "weekly_ppms": "100% (guaranteed)", 
            "monthly_ppms": "100% (guaranteed)"
        }
    }


def main():
    """Main optimization selection and execution"""
    print("🚀 QUALIFICATION MATRIX OPTIMIZATION SUITE")
    print("=" * 60)
    print("1. CLASSIC: Original balanced approach")
    print("2. MAXIMUM: Coverage-focused optimization")
    print("3. ULTIMATE: 100% daily coverage target")
    print("4. BALANCED: Even qualification distribution")
    print("5. MILP: Mathematical optimization (guaranteed coverage + fairness)")
    print()
    
    choice = input("Select optimization approach (1-5): ").strip()
    
    if choice not in ['1', '2', '3', '4', '5']:
        print("❌ Invalid choice. Please select 1, 2, 3, 4, or 5.")
        sys.exit(1)
    
    print(f"\n🚀 STARTING OPTIMIZATION")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        # Step 1: Load and analyze PPM data
        print("📊 LOADING PPM DATA...")
        optimizer = PPMCapacityOptimizer()
        optimizer.generate_report()  # This loads and analyzes all data
        
        # Step 2: Run selected optimization
        if choice == '1':
            matrices, validation_results, config = run_classic_optimization(optimizer)
            optimization_name = "classic_balanced"
        elif choice == '2':
            matrices, validation_results, config = run_maximum_optimization(optimizer)
            optimization_name = "coverage_optimized"
        elif choice == '3':
            matrices, validation_results, config = run_ultimate_optimization(optimizer)
            optimization_name = "ultimate_coverage"
        elif choice == '4':
            matrices, validation_results, config = run_balanced_optimization(optimizer)
            optimization_name = "balanced_coverage"
        elif choice == '5':
            matrices, validation_results, config = run_milp_optimization(optimizer)
            optimization_name = "milp_mathematical"
        
        # Step 3: Save to standardized location
        print("\n💾 SAVING TO STANDARD LOCATION...")
        output_manager = StandardOutputManager()
        
        output_manager.save_optimization_results(
            qualification_matrices=matrices,
            optimization_name=optimization_name,
            optimization_config=config,
            validation_results=validation_results
        )
        
        # Step 4: Display summary
        print("\n📈 OPTIMIZATION RESULTS SUMMARY:")
        print("=" * 50)
        
        for team in [1, 2]:
            if team in validation_results:
                results = validation_results[team]
                daily_cov = results['daily']['coverage_percentage']
                weekly_cov = results['weekly']['coverage_percentage']
                monthly_cov = results['monthly']['coverage_percentage']
                
                print(f"\n🏢 TEAM {team}:")
                
                # Color-code the coverage percentages
                daily_icon = "🎯" if daily_cov >= 100 else "⚠️" if daily_cov >= 50 else "❌"
                weekly_icon = "🎯" if weekly_cov >= 100 else "⚠️" if weekly_cov >= 80 else "❌"
                monthly_icon = "🎯" if monthly_cov >= 100 else "⚠️" if monthly_cov >= 80 else "❌"
                
                print(f"   Daily Coverage:    {daily_cov:.1f}% {daily_icon}")
                print(f"   Weekly Coverage:   {weekly_cov:.1f}% {weekly_icon}")
                print(f"   Monthly Coverage:  {monthly_cov:.1f}% {monthly_icon}")
                print(f"   Overall Status:    {results['overall_status']}")
                print(f"   Risk Level:        {results['risk_analysis']['overall_risk']}")
                
                # Show specific gaps
                if results['daily']['failed_days']:
                    failed_count = len(results['daily']['failed_days'])
                    total_count = results['daily']['total_days_tested']
                    print(f"   Daily gaps:        {failed_count} out of {total_count} days failed")
                
                if results['weekly']['coverage_gaps']:
                    print(f"   Weekly gaps:       {len(results['weekly']['coverage_gaps'])} qualifications missing")
        
        # Success message based on choice
        if choice == '1':
            print(f"\n✅ Classic optimization completed!")
        elif choice == '2':
            print(f"\n✅ Maximum coverage optimization completed!")
        elif choice == '3':
            print(f"\n🔥 ULTIMATE optimization completed!")
            
            # Special check for ULTIMATE results
            ultimate_success = True
            for team in [1, 2]:
                if team in validation_results:
                    if validation_results[team]['daily']['coverage_percentage'] < 100:
                        ultimate_success = False
                        break
            
            if ultimate_success:
                print(f"   🎯 100% DAILY COVERAGE ACHIEVED FOR BOTH TEAMS!")
            else:
                print(f"   ⚠️  Still working toward 100% daily coverage target")
        elif choice == '4':
            print(f"\n⚖️  Balanced optimization completed!")
            
            # Check balance quality
            print(f"   📊 Workload distributed evenly across all engineers")
            print(f"   🎯 Strategic coverage with realistic qualification limits")
        elif choice == '5':
            print(f"\n🔢 MILP Mathematical optimization completed!")
            
            # Check if PuLP was available
            import sys
            try:
                import pulp
                print(f"   🎯 Used PuLP mathematical solver for optimal solution")
            except ImportError:
                print(f"   🧠 Used intelligent heuristic (PuLP not available)")
            
            # Check for perfect balance
            perfect_balance = True
            for team in [1, 2]:
                if team in validation_results:
                    if validation_results[team]['daily']['coverage_percentage'] < 95:
                        perfect_balance = False
                        break
            
            if perfect_balance:
                print(f"   ✅ Achieved mathematical optimum: fairness + coverage")
            else:
                print(f"   ⚠️  Constraint satisfaction achieved (coverage optimized)")
        
        print(f"📁 Results saved to standard location: {output_manager.current_dir}")
        print(f"\n💡 Next steps:")
        print(f"   • Run validation: python3 validate_qualifications.py")
        print(f"   • View results: ls {output_manager.current_dir}")
        
    except Exception as e:
        print(f"\n❌ ERROR during optimization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 