"""
Qualification Matrix Designer
============================

This module creates optimal qualification matrices for maintenance teams,
including role optimization, training prioritization, and capacity validation.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict, Counter
from itertools import combinations
import random
from datetime import datetime, timedelta


class QualificationMatrixDesigner:
    """Design optimal qualification matrices for maintenance teams"""
    
    def __init__(self, optimizer):
        """Initialize with results from PPMCapacityOptimizer"""
        self.optimizer = optimizer
        self.results = optimizer.find_optimal_qualifications()
        self.team_configs = {
            1: {'engineers': 9, 'quals_per_engineer': 10},
            2: {'engineers': 8, 'quals_per_engineer': 11}
        }
        
    def analyze_electrical_vs_mechanical_split(self):
        """Analyze optimal electrical vs mechanical engineer split"""
        print("\n🔧 ELECTRICAL VS MECHANICAL SPLIT ANALYSIS")
        print("=" * 60)
        
        role_analysis = {}
        
        for team in [1, 2]:
            print(f"\n🏢 TEAM {team} ROLE OPTIMIZATION:")
            
            workload = self.results['workload'][team]
            total_engineers = self.team_configs[team]['engineers']
            
            # Calculate electrical vs mechanical hours
            elec_hours = sum([
                workload['daily']['electrical'],
                workload['weekly']['electrical'], 
                workload['monthly']['electrical']
            ])
            
            mech_hours = sum([
                workload['daily']['mechanical'],
                workload['weekly']['mechanical'],
                workload['monthly']['mechanical']
            ])
            
            total_hours = elec_hours + mech_hours
            elec_ratio = elec_hours / total_hours
            mech_ratio = mech_hours / total_hours
            
            # Optimal split based on workload
            optimal_elec = max(1, round(total_engineers * elec_ratio))
            optimal_mech = total_engineers - optimal_elec
            
            # Check daily capacity constraints
            daily_elec = workload['daily']['electrical']
            daily_mech = workload['daily']['mechanical']
            
            min_elec_daily = max(1, np.ceil(daily_elec / 3))
            min_mech_daily = max(1, np.ceil(daily_mech / 3))
            
            # Final recommendations - constrain to available engineers
            recommended_elec = max(optimal_elec, min_elec_daily)
            recommended_mech = max(optimal_mech, min_mech_daily)
            
            # Adjust if total exceeds available engineers
            if recommended_elec + recommended_mech > total_engineers:
                if min_elec_daily + min_mech_daily <= total_engineers:
                    recommended_elec = int(min_elec_daily)
                    recommended_mech = int(min_mech_daily)
                else:
                    # Scale down proportionally while respecting minimums
                    excess = (recommended_elec + recommended_mech) - total_engineers
                    if recommended_elec > min_elec_daily:
                        reduction_elec = min(excess, recommended_elec - min_elec_daily)
                        recommended_elec -= reduction_elec
                        excess -= reduction_elec
                    if excess > 0 and recommended_mech > min_mech_daily:
                        reduction_mech = min(excess, recommended_mech - min_mech_daily)
                        recommended_mech -= reduction_mech
                    
                    print(f"      ⚠️  WARNING: Optimal split needs {int(min_elec_daily + min_mech_daily)} engineers but only have {total_engineers}")
            
            role_analysis[team] = {
                'electrical': int(recommended_elec),
                'mechanical': int(recommended_mech),
                'elec_hours': elec_hours,
                'mech_hours': mech_hours,
                'elec_ratio': elec_ratio,
                'mech_ratio': mech_ratio
            }
            
            print(f"   📊 Workload Distribution:")
            print(f"      Electrical Hours:    {elec_hours:.2f} ({elec_ratio:.1%})")
            print(f"      Mechanical Hours:    {mech_hours:.2f} ({mech_ratio:.1%})")
            print(f"      Total Hours:         {total_hours:.2f}")
            
            print(f"\n   👥 Optimal Engineer Split:")
            print(f"      Electrical Engineers: {recommended_elec}")
            print(f"      Mechanical Engineers: {recommended_mech}")
            print(f"      Total Engineers:      {recommended_elec + recommended_mech}")
            
            print(f"\n   ⏱️  Daily Capacity Check:")
            print(f"      Elec Daily Need:     {daily_elec:.2f}hrs → {min_elec_daily} engineers min")
            print(f"      Mech Daily Need:     {daily_mech:.2f}hrs → {min_mech_daily} engineers min")
            print(f"      Status:              {'✅ FEASIBLE' if recommended_elec + recommended_mech <= total_engineers else '❌ NEED MORE ENGINEERS'}")
        
        return role_analysis
    
    def create_qualification_matrix(self, role_analysis):
        """Create detailed qualification matrix for each team"""
        print("\n📋 QUALIFICATION MATRIX DESIGN")
        print("=" * 60)
        
        matrices = {}
        
        for team in [1, 2]:
            print(f"\n🏢 TEAM {team} QUALIFICATION MATRIX:")
            
            # Get qualifications for this team
            team_quals = list(self.results['qualifications'][team]['all'])
            
            # Role split
            elec_engineers = int(role_analysis[team]['electrical'])
            mech_engineers = int(role_analysis[team]['mechanical'])
            total_engineers = elec_engineers + mech_engineers
            
            # Separate electrical and mechanical qualifications
            elec_quals = [q for q in team_quals if '.DE.' in q or '.ME.' in q or '.WE.' in q]
            mech_quals = [q for q in team_quals if '.DM.' in q or '.MM.' in q or '.WM.' in q]
            shared_quals = [q for q in team_quals if q not in elec_quals and q not in mech_quals]
            
            print(f"   📊 Qualification Categories:")
            print(f"      Electrical Quals:    {len(elec_quals)}")
            print(f"      Mechanical Quals:    {len(mech_quals)}")
            print(f"      Shared/Other Quals:  {len(shared_quals)}")
            print(f"      Total Qualifications: {len(team_quals)}")
            
            # Create engineer assignments
            engineer_assignments = {}
            
            # Create electrical engineers
            for i in range(elec_engineers):
                engineer_id = f"TEAM{team}_ELEC_{i+1:02d}"
                engineer_assignments[engineer_id] = {
                    'role': 'electrical',
                    'qualifications': [],
                    'type_a_rides': [],
                    'daily_ppms': [],
                    'weekly_ppms': [],
                    'monthly_ppms': []
                }
            
            # Create mechanical engineers  
            for i in range(mech_engineers):
                engineer_id = f"TEAM{team}_MECH_{i+1:02d}"
                engineer_assignments[engineer_id] = {
                    'role': 'mechanical',
                    'qualifications': [],
                    'type_a_rides': [],
                    'daily_ppms': [],
                    'weekly_ppms': [],
                    'monthly_ppms': []
                }
            
            # Assign Type A rides (2 per engineer constraint)
            type_a_rides = self.results['team_composition'][team]['A']
            engineers_list = list(engineer_assignments.keys())
            
            # Distribute Type A rides evenly
            type_a_assignments = []
            for ride in type_a_rides:
                for _ in range(2):  # Each ride can be assigned to multiple engineers
                    type_a_assignments.append(ride)
            
            # Shuffle and assign
            random.shuffle(engineers_list)
            random.shuffle(type_a_assignments)
            
            for i, engineer in enumerate(engineers_list):
                # Assign 2 Type A rides per engineer
                assigned_rides = type_a_assignments[i*2:(i*2)+2] if (i*2)+2 <= len(type_a_assignments) else type_a_assignments[i*2:]
                engineer_assignments[engineer]['type_a_rides'] = assigned_rides
            
            # Distribute qualifications optimally
            self._distribute_qualifications(engineer_assignments, elec_quals, mech_quals, shared_quals, team)
            
            matrices[team] = engineer_assignments
            
            # Display matrix summary
            print(f"\n   👥 ENGINEER ASSIGNMENTS:")
            for engineer_id, assignment in engineer_assignments.items():
                role = assignment['role']
                qual_count = len(assignment['qualifications'])
                type_a_count = len(assignment['type_a_rides'])
                print(f"      {engineer_id}: {role.upper()}, {qual_count} quals, {type_a_count} Type A rides")
        
        return matrices
    
    def _distribute_qualifications(self, engineer_assignments, elec_quals, mech_quals, shared_quals, team):
        """Optimally distribute qualifications among engineers"""
        
        # Get target qualifications per engineer
        target_quals = self.team_configs[team]['quals_per_engineer']
        
        # Electrical engineers get electrical quals + some shared
        elec_engineers = [e for e, a in engineer_assignments.items() if a['role'] == 'electrical']
        mech_engineers = [e for e, a in engineer_assignments.items() if a['role'] == 'mechanical']
        
        # Distribute electrical qualifications
        if elec_engineers and elec_quals:
            elec_quals_per_eng = max(1, len(elec_quals) // len(elec_engineers))
            for i, engineer in enumerate(elec_engineers):
                start_idx = i * elec_quals_per_eng
                end_idx = min(start_idx + elec_quals_per_eng, len(elec_quals))
                engineer_assignments[engineer]['qualifications'].extend(elec_quals[start_idx:end_idx])
        
        # Distribute mechanical qualifications
        if mech_engineers and mech_quals:
            mech_quals_per_eng = max(1, len(mech_quals) // len(mech_engineers))
            for i, engineer in enumerate(mech_engineers):
                start_idx = i * mech_quals_per_eng
                end_idx = min(start_idx + mech_quals_per_eng, len(mech_quals))
                engineer_assignments[engineer]['qualifications'].extend(mech_quals[start_idx:end_idx])
        
        # Distribute shared qualifications to fill up to target
        all_engineers = list(engineer_assignments.keys())
        shared_idx = 0
        
        for engineer in all_engineers:
            current_quals = len(engineer_assignments[engineer]['qualifications'])
            needed_quals = target_quals - current_quals
            
            if needed_quals > 0 and shared_idx < len(shared_quals):
                end_shared = min(shared_idx + needed_quals, len(shared_quals))
                engineer_assignments[engineer]['qualifications'].extend(shared_quals[shared_idx:end_shared])
                shared_idx = end_shared
    
    def design_training_plan(self, matrices):
        """Design prioritized training plan"""
        print("\n🎓 TRAINING PLAN DESIGN")
        print("=" * 60)
        
        training_plans = {}
        
        for team in [1, 2]:
            print(f"\n🏢 TEAM {team} TRAINING PRIORITIZATION:")
            
            # Analyze qualification criticality
            daily_quals = self.results['qualifications'][team]['daily']
            weekly_quals = self.results['qualifications'][team]['weekly'] 
            monthly_quals = self.results['qualifications'][team]['monthly']
            
            # Priority levels
            priority_map = {}
            for qual in daily_quals:
                priority_map[qual] = 1  # Highest priority
            for qual in weekly_quals:
                if qual not in priority_map:
                    priority_map[qual] = 2  # Medium priority
            for qual in monthly_quals:
                if qual not in priority_map:
                    priority_map[qual] = 3  # Lower priority
            
            # Create training phases
            training_phases = {
                'Phase 1 (Immediate)': {'qualifications': [], 'description': 'Critical daily PPMs'},
                'Phase 2 (Month 2-3)': {'qualifications': [], 'description': 'Weekly PPMs and essential skills'},
                'Phase 3 (Month 4-6)': {'qualifications': [], 'description': 'Monthly PPMs and specializations'},
                'Phase 4 (Ongoing)': {'qualifications': [], 'description': 'Advanced qualifications and cross-training'}
            }
            
            # Sort by priority and assign to phases
            all_quals = list(self.results['qualifications'][team]['all'])
            sorted_quals = sorted(all_quals, key=lambda q: (priority_map.get(q, 4), q))
            
            # Distribute qualifications across phases
            phase_keys = list(training_phases.keys())
            quals_per_phase = len(sorted_quals) // len(phase_keys)
            
            for i, qual in enumerate(sorted_quals):
                phase_idx = min(i // max(1, quals_per_phase), len(phase_keys) - 1)
                phase_key = phase_keys[phase_idx]
                training_phases[phase_key]['qualifications'].append(qual)
            
            # Engineer-specific training plans
            engineer_plans = {}
            for engineer_id, assignment in matrices[team].items():
                engineer_plans[engineer_id] = {
                    'phase_1': [],
                    'phase_2': [],
                    'phase_3': [],
                    'phase_4': [],
                    'estimated_weeks': 0
                }
                
                # Assign engineer's qualifications to appropriate phases
                for qual in assignment['qualifications']:
                    priority = priority_map.get(qual, 4)
                    if priority == 1:
                        engineer_plans[engineer_id]['phase_1'].append(qual)
                    elif priority == 2:
                        engineer_plans[engineer_id]['phase_2'].append(qual)
                    elif priority == 3:
                        engineer_plans[engineer_id]['phase_3'].append(qual)
                    else:
                        engineer_plans[engineer_id]['phase_4'].append(qual)
                
                # Estimate training time (assume 1 week per qualification)
                total_quals = len(assignment['qualifications'])
                engineer_plans[engineer_id]['estimated_weeks'] = total_quals
            
            training_plans[team] = {
                'phases': training_phases,
                'engineer_plans': engineer_plans
            }
            
            # Display training plan summary
            print(f"   📅 TRAINING PHASES:")
            for phase, details in training_phases.items():
                qual_count = len(details['qualifications'])
                print(f"      {phase}: {qual_count} qualifications")
                print(f"         {details['description']}")
            
            print(f"\n   👤 ENGINEER TRAINING ESTIMATES:")
            for engineer_id, plan in engineer_plans.items():
                phase1_count = len(plan['phase_1'])
                total_weeks = plan['estimated_weeks']
                print(f"      {engineer_id}: {phase1_count} critical quals, ~{total_weeks} weeks total")
        
        return training_plans
    
    def validate_capacity_coverage(self, matrices, training_plans):
        """Validate that the qualification matrix provides adequate coverage"""
        print("\n✅ CAPACITY VALIDATION MODEL")
        print("=" * 60)
        
        validation_results = {}
        
        for team in [1, 2]:
            print(f"\n🏢 TEAM {team} COVERAGE VALIDATION:")
            
            # Check daily PPM coverage
            daily_coverage = self._validate_daily_coverage(team, matrices[team])
            weekly_coverage = self._validate_weekly_coverage(team, matrices[team])
            monthly_coverage = self._validate_monthly_coverage(team, matrices[team])
            
            # Risk analysis
            risk_analysis = self._analyze_coverage_risks(team, matrices[team])
            
            validation_results[team] = {
                'daily_coverage': daily_coverage,
                'weekly_coverage': weekly_coverage,
                'monthly_coverage': monthly_coverage,
                'risk_analysis': risk_analysis
            }
            
            print(f"   📊 COVERAGE SUMMARY:")
            print(f"      Daily PPMs:     {daily_coverage['coverage_pct']:.1f}% coverage")
            print(f"      Weekly PPMs:    {weekly_coverage['coverage_pct']:.1f}% coverage") 
            print(f"      Monthly PPMs:   {monthly_coverage['coverage_pct']:.1f}% coverage")
            print(f"      Risk Level:     {risk_analysis['overall_risk']}")
        
        return validation_results
    
    def _validate_daily_coverage(self, team, engineer_assignments):
        """Validate daily PPM coverage"""
        daily_ppms = []
        for ride_id, ppm_data in self.optimizer.ppms_by_type['daily'].items():
            if ride_id in self.optimizer.rides_info and self.optimizer.rides_info[ride_id]['team_responsible'] == team:
                daily_ppms.extend(ppm_data['ppms'])
        
        # Check which PPMs can be covered
        covered_ppms = 0
        total_ppms = len(daily_ppms)
        
        for ppm in daily_ppms:
            required_qual = ppm['qualification_code']
            can_cover = any(required_qual in assignment['qualifications'] 
                          for assignment in engineer_assignments.values())
            if can_cover:
                covered_ppms += 1
        
        coverage_pct = (covered_ppms / total_ppms * 100) if total_ppms > 0 else 100
        
        return {
            'total_ppms': total_ppms,
            'covered_ppms': covered_ppms,
            'coverage_pct': coverage_pct,
            'uncovered_quals': []  # Could be enhanced to track specific gaps
        }
    
    def _validate_weekly_coverage(self, team, engineer_assignments):
        """Validate weekly PPM coverage"""
        # Similar logic to daily but for weekly PPMs
        weekly_ppms = []
        for ride_id, ppm_data in self.optimizer.ppms_by_type['weekly'].items():
            if ride_id in self.optimizer.rides_info and self.optimizer.rides_info[ride_id]['team_responsible'] == team:
                weekly_ppms.extend(ppm_data['ppms'])
        
        covered_ppms = sum(1 for ppm in weekly_ppms 
                          if any(ppm['qualification_code'] in assignment['qualifications'] 
                                for assignment in engineer_assignments.values()))
        
        coverage_pct = (covered_ppms / len(weekly_ppms) * 100) if weekly_ppms else 100
        
        return {
            'total_ppms': len(weekly_ppms),
            'covered_ppms': covered_ppms,
            'coverage_pct': coverage_pct
        }
    
    def _validate_monthly_coverage(self, team, engineer_assignments):
        """Validate monthly PPM coverage"""
        # Similar logic for monthly PPMs
        monthly_ppms = []
        for ride_id, ppm_data in self.optimizer.ppms_by_type['monthly'].items():
            if ride_id in self.optimizer.rides_info and self.optimizer.rides_info[ride_id]['team_responsible'] == team:
                monthly_ppms.extend(ppm_data['ppms'])
        
        covered_ppms = sum(1 for ppm in monthly_ppms 
                          if any(ppm['qualification_code'] in assignment['qualifications'] 
                                for assignment in engineer_assignments.values()))
        
        coverage_pct = (covered_ppms / len(monthly_ppms) * 100) if monthly_ppms else 100
        
        return {
            'total_ppms': len(monthly_ppms),
            'covered_ppms': covered_ppms,
            'coverage_pct': coverage_pct
        }
    
    def _analyze_coverage_risks(self, team, engineer_assignments):
        """Analyze coverage risks and redundancy"""
        
        # Count how many engineers have each qualification
        qual_coverage = defaultdict(int)
        for assignment in engineer_assignments.values():
            for qual in assignment['qualifications']:
                qual_coverage[qual] += 1
        
        # Identify single points of failure
        single_point_failures = [qual for qual, count in qual_coverage.items() if count == 1]
        good_coverage = [qual for qual, count in qual_coverage.items() if count >= 2]
        excellent_coverage = [qual for qual, count in qual_coverage.items() if count >= 3]
        
        # Calculate risk level
        total_quals = len(qual_coverage)
        spf_ratio = len(single_point_failures) / total_quals if total_quals > 0 else 0
        
        if spf_ratio > 0.3:
            risk_level = "HIGH"
        elif spf_ratio > 0.1:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return {
            'single_point_failures': len(single_point_failures),
            'good_coverage': len(good_coverage),
            'excellent_coverage': len(excellent_coverage),
            'overall_risk': risk_level,
            'spf_ratio': spf_ratio
        }
    
    def export_results(self, matrices, training_plans, validation_results):
        """Export all results to files"""
        print("\n💾 EXPORTING RESULTS")
        print("=" * 40)
        
        output_dir = Path("outputs/qualification_optimization")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Export qualification matrices
        for team, matrix in matrices.items():
            matrix_file = output_dir / f"team_{team}_qualification_matrix.json"
            with open(matrix_file, 'w') as f:
                json.dump(matrix, f, indent=2)
            print(f"   📋 Exported: {matrix_file}")
        
        # Export training plans
        for team, plan in training_plans.items():
            plan_file = output_dir / f"team_{team}_training_plan.json"
            with open(plan_file, 'w') as f:
                json.dump(plan, f, indent=2)
            print(f"   🎓 Exported: {plan_file}")
        
        # Export validation results
        validation_file = output_dir / "capacity_validation.json"
        with open(validation_file, 'w') as f:
            json.dump(validation_results, f, indent=2)
        print(f"   ✅ Exported: {validation_file}")
        
        # Create summary report
        self._create_summary_report(output_dir, matrices, training_plans, validation_results)
        
        print(f"\n📁 All results exported to: {output_dir}")
    
    def _create_summary_report(self, output_dir, matrices, training_plans, validation_results):
        """Create a comprehensive summary report"""
        report_file = output_dir / "optimization_summary_report.md"
        
        with open(report_file, 'w') as f:
            f.write("# Theme Park Maintenance Qualification Optimization Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Executive Summary\n\n")
            for team in [1, 2]:
                engineers = len(matrices[team])
                total_quals = sum(len(a['qualifications']) for a in matrices[team].values())
                daily_coverage = validation_results[team]['daily_coverage']['coverage_pct']
                
                f.write(f"### Team {team}\n")
                f.write(f"- Engineers: {engineers}\n")
                f.write(f"- Total Qualifications: {total_quals}\n")
                f.write(f"- Daily PPM Coverage: {daily_coverage:.1f}%\n")
                f.write(f"- Risk Level: {validation_results[team]['risk_analysis']['overall_risk']}\n\n")
        
        print(f"   📊 Exported: {report_file}")
    
    def run_complete_analysis(self):
        """Run the complete qualification optimization analysis"""
        print("\n" + "="*80)
        print("🎯 COMPREHENSIVE QUALIFICATION OPTIMIZATION ANALYSIS")
        print("="*80)
        
        # Step 1: Analyze role split
        role_analysis = self.analyze_electrical_vs_mechanical_split()
        
        # Step 2: Create qualification matrix
        matrices = self.create_qualification_matrix(role_analysis)
        
        # Step 3: Design training plan
        training_plans = self.design_training_plan(matrices)
        
        # Step 4: Validate capacity coverage
        validation_results = self.validate_capacity_coverage(matrices, training_plans)
        
        # Step 5: Export all results
        self.export_results(matrices, training_plans, validation_results)
        
        print("\n🎉 COMPLETE ANALYSIS FINISHED!")
        print("✅ All 4 optimization components completed successfully")
        
        return {
            'role_analysis': role_analysis,
            'qualification_matrices': matrices,
            'training_plans': training_plans,
            'validation_results': validation_results
        }


def main():
    """Run complete qualification optimization"""
    # Import the base optimizer
    import sys
    sys.path.append('src/analysis')
    from ppm_capacity_optimizer import PPMCapacityOptimizer
    
    # Create base optimizer
    optimizer = PPMCapacityOptimizer()
    
    # Create qualification matrix designer
    designer = QualificationMatrixDesigner(optimizer)
    
    # Run complete analysis
    results = designer.run_complete_analysis()
    
    return designer, results


if __name__ == "__main__":
    designer, results = main() 