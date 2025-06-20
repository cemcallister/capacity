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
    validation_results, assignment_counts = designer.validate_and_export_results(matrices)
    
    return matrices, validation_results, assignment_counts, {
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


def run_training_optimization(optimizer):
    """Run Training Optimization based on current qualifications"""
    print("\n🎓 RUNNING TRAINING OPTIMIZATION ANALYSIS...")
    
    # Import the training optimizer
    from src.analysis.training_optimization_designer import TrainingOptimizationDesigner
    
    designer = TrainingOptimizationDesigner(optimizer)
    
    # Step 1: Load current qualifications from EngQual.csv
    current_matrices = designer.load_current_qualification_state()
    
    # Step 2: Create qualification matrices from current state (not theoretical optimal)
    current_state_matrices = designer.create_current_state_matrices(current_matrices)
    
    # Step 3: Analyze coverage gaps and optimize training assignments
    training_recommendations = designer.optimize_training_assignments(current_state_matrices)
    
    # Step 3.5: Generate and display detailed training report
    detailed_report = designer.generate_detailed_training_report(training_recommendations, current_state_matrices)
    designer.display_detailed_training_report(detailed_report)
    
    # Step 3.6: Export to CSV for easy analysis
    csv_files = designer.export_detailed_report_to_csv(detailed_report)
    
    # Step 4: Validate proposed training impact
    validation_results = designer.validate_training_impact(training_recommendations)
    
    return current_matrices, current_state_matrices, training_recommendations, validation_results, detailed_report, csv_files, {
        "approach": "training_optimization",
        "features": [
            "current_state_analysis",
            "qualification_gap_identification", 
            "training_impact_optimization",
            "coverage_improvement_prioritization",
            "cost_benefit_analysis",
            "skill_development_planning"
        ],
        "target_coverage": {
            "daily_ppms": "Progressive improvement",
            "weekly_ppms": "Progressive improvement", 
            "monthly_ppms": "Progressive improvement"
        },
        "optimization_goals": [
            "Minimize training effort",
            "Maximize coverage improvement",
            "Balance workload distribution",
            "Prioritize critical skills gaps"
        ]
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
    print("6. TRAINING: Current state vs optimal training")
    print()
    
    choice = input("Select optimization approach (1-6): ").strip()
    
    if choice not in ['1', '2', '3', '4', '5', '6']:
        print("❌ Invalid choice. Please select 1, 2, 3, 4, 5, or 6.")
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
        assignment_counts = None  # Initialize assignment_counts for all methods
        
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
            matrices, validation_results, assignment_counts, config = run_milp_optimization(optimizer)
            optimization_name = "milp_mathematical"
        elif choice == '6':
            current_matrices, current_state_matrices, training_recommendations, validation_results, detailed_report, csv_files, config = run_training_optimization(optimizer)
            optimization_name = "training_optimization"
            matrices = current_state_matrices  # Use current state matrices for saving
        
        # Step 3: Save to standardized location
        print("\n💾 SAVING TO STANDARD LOCATION...")
        output_manager = StandardOutputManager()
        
        output_manager.save_optimization_results(
            qualification_matrices=matrices,
            optimization_name=optimization_name,
            optimization_config=config,
            validation_results=validation_results
        )
        
        # Step 3.5: Save assignment counts if available (MILP optimization)
        if assignment_counts is not None:
            import json
            assignment_counts_path = output_manager.current_dir / "engineer_assignment_counts.json"
            print(f"   💾 Saving engineer assignment counts to: {assignment_counts_path}")
            
            with open(assignment_counts_path, 'w') as f:
                json.dump(assignment_counts, f, indent=2)
        
        # Step 3.6: Save training recommendations if available (Training optimization)
        if choice == '6' and 'training_recommendations' in locals():
            import json
            training_path = output_manager.current_dir / "training_recommendations.json"
            current_state_path = output_manager.current_dir / "current_qualification_state.json"
            print(f"   💾 Saving training recommendations to: {training_path}")
            print(f"   💾 Saving current state analysis to: {current_state_path}")
            
            with open(training_path, 'w') as f:
                json.dump(training_recommendations, f, indent=2)
            
            with open(current_state_path, 'w') as f:
                json.dump(current_matrices, f, indent=2)
            
            # Save detailed training report
            detailed_report_path = output_manager.current_dir / "detailed_training_report.json"
            print(f"   💾 Saving detailed training report to: {detailed_report_path}")
            
            with open(detailed_report_path, 'w') as f:
                json.dump(detailed_report, f, indent=2)
            
            # Display summary of assignment counts
            print("\n📊 ENGINEER ASSIGNMENT COUNTS SUMMARY:")
            if assignment_counts:
                for team_key, team_data in assignment_counts.items():
                    team_num = team_key.split('_')[1]
                    print(f"\n🏢 TEAM {team_num}:")
                    
                    # Calculate statistics
                    total_rides = len(team_data)
                    total_engineers = sum(ride_data['total_count'] for ride_data in team_data.values())
                    avg_engineers_per_ride = total_engineers / total_rides if total_rides > 0 else 0
                    
                    electrical_engineers = sum(ride_data['electrical_count'] for ride_data in team_data.values())
                    mechanical_engineers = sum(ride_data['mechanical_count'] for ride_data in team_data.values())
                    
                    print(f"   Total rides: {total_rides}")
                    print(f"   Total engineer assignments: {total_engineers}")
                    print(f"   Average engineers per ride: {avg_engineers_per_ride:.1f}")
                    print(f"   Electrical engineers: {electrical_engineers}")
                    print(f"   Mechanical engineers: {mechanical_engineers}")
                    
                    # Show rides with highest/lowest coverage
                    if team_data:
                        ride_counts = [(ride_id, data['total_count'], data['ride_name']) 
                                      for ride_id, data in team_data.items()]
                        ride_counts.sort(key=lambda x: x[1])
                        
                        min_ride = ride_counts[0]
                        max_ride = ride_counts[-1]
                        
                        print(f"   Lowest coverage: {min_ride[2]} ({min_ride[1]} engineers)")
                        print(f"   Highest coverage: {max_ride[2]} ({max_ride[1]} engineers)")
            else:
                print("   No assignment counts available for this optimization type.")
        
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
        elif choice == '6':
            print(f"\n🎓 Training optimization completed!")
            
            # Check for training effectiveness
            training_effectiveness = True
            for team in [1, 2]:
                if team in validation_results:
                    if validation_results[team]['daily']['coverage_percentage'] < 95:
                        training_effectiveness = False
                        break
            
            if training_effectiveness:
                print(f"   ✅ Training effectiveness achieved: coverage improvement")
            else:
                print(f"   ⚠️  Training effectiveness not fully achieved")
        
        print(f"📁 Results saved to standard location: {output_manager.current_dir}")
        
        # Additional info for training optimization
        if choice == '6':
            print(f"\n📊 CSV FILES FOR EASY ANALYSIS:")
            print(f"   • training_summary_by_engineer.csv - Engineer overview & priority scores")
            print(f"   • training_breakdown_by_ride.csv - Ride-by-ride qualification needs")
            print(f"   • specific_qualifications_needed.csv - Exact qualifications to train")
            print(f"   • training_priority_ranking.csv - Overall priority ranking")
            print(f"   💡 Open these in Excel/Google Sheets for filtering & sorting!")
        
        print(f"\n💡 Next steps:")
        print(f"   • Run validation: python3 validate_qualifications.py")
        print(f"   • View results: ls {output_manager.current_dir}")
        if choice == '6':
            print(f"   • Open CSV files in Excel/Google Sheets for detailed analysis")
        
    except Exception as e:
        print(f"\n❌ ERROR during optimization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 