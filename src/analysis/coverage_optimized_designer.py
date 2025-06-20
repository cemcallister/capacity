"""
Coverage-Optimized Qualification Designer
=========================================

This module creates qualification matrices that pass operational coverage validation
by accounting for:
- Multiple engineers needed for high-duration daily PPMs
- Shift pattern coverage requirements  
- Adequate redundancy for critical maintenance
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict, Counter
from itertools import combinations
import random
import math
from datetime import datetime

# Import the coverage validation framework
try:
    from .coverage_validator import CoverageValidator
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from coverage_validator import CoverageValidator


class CoverageOptimizedDesigner:
    """Create qualification matrices that meet operational coverage requirements"""
    
    def __init__(self, optimizer_results):
        """Initialize with PPM and ride data"""
        self.optimizer = optimizer_results
        self.engineers = self._load_engineer_data()
        self.coverage_validator = CoverageValidator(optimizer_results)
        
        # Enhanced analysis for better coverage
        self.ppm_requirements = self._analyze_ppm_requirements()
        self.shift_analysis = self._analyze_shift_patterns()
        
        # Set random seed for deterministic results
        random.seed(42)
        np.random.seed(42)
        
    def _load_engineer_data(self):
        """Load real engineer data from JSON files"""
        engineers = {1: {'electrical': [], 'mechanical': []}, 2: {'electrical': [], 'mechanical': []}}
        
        # Load Team 1 engineers
        with open('data/processed/engineers/team1_elec_engineers.json', 'r') as f:
            team1_elec = json.load(f)
            engineers[1]['electrical'] = team1_elec['engineers']
            
        with open('data/processed/engineers/team1_mech_engineers.json', 'r') as f:
            team1_mech = json.load(f)
            engineers[1]['mechanical'] = team1_mech['engineers']
            
        # Load Team 2 engineers  
        with open('data/processed/engineers/team2_elec_engineers.json', 'r') as f:
            team2_elec = json.load(f)
            engineers[2]['electrical'] = [eng for eng in team2_elec['engineers'] if eng.get('active', True)]
            
        with open('data/processed/engineers/team2_mech_engineers.json', 'r') as f:
            team2_mech = json.load(f)
            engineers[2]['mechanical'] = [eng for eng in team2_mech['engineers'] if not eng.get('vacancy', False)]
            
        return engineers
    
    def _analyze_ppm_requirements(self):
        """Analyze PPM requirements to determine multi-engineer needs"""
        print("🔍 ANALYZING PPM REQUIREMENTS FOR MULTI-ENGINEER NEEDS")
        print("=" * 70)
        
        requirements = {}
        
        for team in [1, 2]:
            requirements[team] = {}
            team_rides = [rid for rid, info in self.optimizer.rides_info.items() 
                         if info.get('team_responsible') == team]
            
            print(f"\n🏢 TEAM {team} PPM ANALYSIS:")
            
            for ride_id in team_rides:
                requirements[team][ride_id] = {
                    'daily': {'electrical': 0, 'mechanical': 0},
                    'weekly': {'electrical': 0, 'mechanical': 0},
                    'monthly': {'electrical': 0, 'mechanical': 0}
                }
                
                # Analyze daily PPMs (critical - need multiple engineers if total > 3 hours)
                if ride_id in self.optimizer.ppms_by_type['daily']:
                    daily_ppms = self.optimizer.ppms_by_type['daily'][ride_id]['ppms']
                    
                    # Group by maintenance type
                    elec_duration = sum(ppm['duration_hours'] for ppm in daily_ppms 
                                       if ppm['maintenance_type'] == 'ELECTRICAL')
                    mech_duration = sum(ppm['duration_hours'] for ppm in daily_ppms 
                                       if ppm['maintenance_type'] == 'MECHANICAL')
                    
                    # Calculate engineers needed (based on 3-hour window)
                    elec_engineers_needed = math.ceil(elec_duration / 3.0) if elec_duration > 0 else 0
                    mech_engineers_needed = math.ceil(mech_duration / 3.0) if mech_duration > 0 else 0
                    
                    requirements[team][ride_id]['daily']['electrical'] = elec_engineers_needed
                    requirements[team][ride_id]['daily']['mechanical'] = mech_engineers_needed
                    
                    if elec_engineers_needed > 1 or mech_engineers_needed > 1:
                        print(f"   ⚠️  {ride_id} DAILY: E={elec_duration:.1f}h→{elec_engineers_needed} eng, M={mech_duration:.1f}h→{mech_engineers_needed} eng")
                
                # Weekly and monthly PPMs need 1 engineer each (flexible scheduling)
                for ppm_type in ['weekly', 'monthly']:
                    if ride_id in self.optimizer.ppms_by_type[ppm_type]:
                        ppms = self.optimizer.ppms_by_type[ppm_type][ride_id]['ppms']
                        
                        elec_ppms = [ppm for ppm in ppms if ppm['maintenance_type'] == 'ELECTRICAL']
                        mech_ppms = [ppm for ppm in ppms if ppm['maintenance_type'] == 'MECHANICAL']
                        
                        # Each PPM needs at least 1 qualified engineer
                        elec_engineers_needed = 1 if elec_ppms else 0
                        mech_engineers_needed = 1 if mech_ppms else 0
                        
                        requirements[team][ride_id][ppm_type]['electrical'] = elec_engineers_needed
                        requirements[team][ride_id][ppm_type]['mechanical'] = mech_engineers_needed
        
        return requirements
    
    def _analyze_shift_patterns(self):
        """Analyze shift patterns to optimize engineer-shift matching"""
        print("📅 ANALYZING SHIFT PATTERNS FOR OPTIMIZATION")
        
        shift_analysis = {}
        
        for team in [1, 2]:
            shift_analysis[team] = {'electrical': {}, 'mechanical': {}}
            
            # Load rota data
            for role in ['electrical', 'mechanical']:
                rota_file = f'data/processed/parsed_rotas/parsed_team{team}_{"elec" if role == "electrical" else "mech"}_rota.json'
                try:
                    with open(rota_file, 'r') as f:
                        rota_data = json.load(f)
                    
                    # Analyze early shift availability (critical for daily PPMs)
                    engineer_early_days = {}
                    
                    for week_key, week_data in rota_data.items():
                        for engineer_id, shifts in week_data.items():
                            if engineer_id not in engineer_early_days:
                                engineer_early_days[engineer_id] = 0
                            
                            # Count early shifts Monday-Friday
                            for day_idx in range(5):
                                if day_idx < len(shifts) and shifts[day_idx] == 'E':
                                    engineer_early_days[engineer_id] += 1
                    
                    shift_analysis[team][role] = engineer_early_days
                    
                    # Show top engineers for early shift coverage
                    sorted_engineers = sorted(engineer_early_days.items(), key=lambda x: x[1], reverse=True)
                    print(f"   Team {team} {role}: Top early shift engineers: {sorted_engineers[:3]}")
                    
                except FileNotFoundError:
                    print(f"   ⚠️  Rota file not found for Team {team} {role}")
                    shift_analysis[team][role] = {}
        
        return shift_analysis
    
    def create_optimized_qualification_matrices(self):
        """Create qualification matrices optimized for operational coverage"""
        print("\n🎯 CREATING COVERAGE-OPTIMIZED QUALIFICATION MATRICES")
        print("=" * 70)
        
        matrices = {}
        
        for team in [1, 2]:
            print(f"\n🏢 TEAM {team} OPTIMIZATION:")
            
            # Get active engineers
            elec_engineers = [eng for eng in self.engineers[team]['electrical'] if eng.get('active', True)]
            mech_engineers = [eng for eng in self.engineers[team]['mechanical'] if not eng.get('vacancy', False)]
            
            print(f"   👥 Available Engineers: {len(elec_engineers)} electrical, {len(mech_engineers)} mechanical")
            
            # Initialize engineer assignments
            engineer_assignments = {}
            
            # Create engineer records with shift analysis
            for engineer in elec_engineers:
                engineer_id = engineer['employee_code']
                early_shift_days = self.shift_analysis[team]['electrical'].get(engineer_id, 0)
                engineer_assignments[engineer_id] = {
                    'name': engineer['timeplan_name'],
                    'role': 'electrical',
                    'rota_number': engineer['rota_number'],
                    'early_shift_days': early_shift_days,
                    'assigned_rides': [],
                    'type_a_rides': [],
                    'type_b_rides': [],
                    'type_c_rides': [],
                    'qualifications': [],
                    'daily_ppms': [],
                    'weekly_ppms': [],
                    'monthly_ppms': []
                }
            
            for engineer in mech_engineers:
                engineer_id = engineer['employee_code']
                early_shift_days = self.shift_analysis[team]['mechanical'].get(engineer_id, 0)
                engineer_assignments[engineer_id] = {
                    'name': engineer['timeplan_name'],
                    'role': 'mechanical',
                    'rota_number': engineer['rota_number'],
                    'early_shift_days': early_shift_days,
                    'assigned_rides': [],
                    'type_a_rides': [],
                    'type_b_rides': [],
                    'type_c_rides': [],
                    'qualifications': [],
                    'daily_ppms': [],
                    'weekly_ppms': [],
                    'monthly_ppms': []
                }
            
            # Get team rides by type
            team_rides = [rid for rid, info in self.optimizer.rides_info.items() 
                         if info.get('team_responsible') == team]
            
            type_a_rides = [rid for rid in team_rides if self.optimizer.rides_info[rid]['type'] == 'A']
            type_b_rides = [rid for rid in team_rides if self.optimizer.rides_info[rid]['type'] == 'B']
            type_c_rides = [rid for rid in team_rides if self.optimizer.rides_info[rid]['type'] == 'C']
            
            print(f"   🎯 Rides: {len(type_a_rides)}A, {len(type_b_rides)}B, {len(type_c_rides)}C")
            
            # STEP 1: Assign Type A rides (each engineer gets exactly 2)
            self._assign_type_a_rides(engineer_assignments, type_a_rides, team)
            
            # STEP 2: Assign Type B/C rides with adequate coverage for daily PPMs
            self._assign_type_bc_rides_with_coverage(engineer_assignments, type_b_rides + type_c_rides, team)
            
            # STEP 3: Assign qualifications based on role and requirements
            self._assign_qualifications(engineer_assignments, team)
            
            # STEP 4: Iterative improvement based on validation feedback
            engineer_assignments = self._iterative_improvement(engineer_assignments, team)
            
            matrices[team] = engineer_assignments
            
            # Display summary
            self._display_assignment_summary(engineer_assignments, team)
        
        return matrices
    
    def _assign_type_a_rides(self, engineer_assignments, type_a_rides, team):
        """Assign Type A rides ensuring each engineer gets exactly 2, prioritizing early shift engineers"""
        print(f"\n   🎯 TYPE A ASSIGNMENT (2 per engineer, early shift priority):")
        
        engineers_list = list(engineer_assignments.keys())
        total_engineers = len(engineers_list)
        
        if total_engineers == 0:
            print("      ⚠️  No engineers available!")
            return
        
        # Sort engineers by early shift days (better for daily PPMs) 
        engineers_by_early_shifts = sorted(engineers_list, 
                                          key=lambda e: engineer_assignments[e]['early_shift_days'], 
                                          reverse=True)
        
        # Create assignment pool - each ride repeated to give each engineer 2 rides
        assignments_needed = total_engineers * 2
        assignments_per_ride = assignments_needed // len(type_a_rides)
        extra_assignments = assignments_needed % len(type_a_rides)
        
        type_a_pool = []
        for i, ride in enumerate(type_a_rides):
            count = assignments_per_ride + (1 if i < extra_assignments else 0)
            type_a_pool.extend([ride] * count)
        
        random.shuffle(type_a_pool)
        
        # Assign 2 rides to each engineer (prioritizing early shift availability)
        for i, engineer_id in enumerate(engineers_by_early_shifts):
            start_idx = i * 2
            assigned_rides = type_a_pool[start_idx:start_idx + 2] if start_idx + 1 < len(type_a_pool) else type_a_pool[start_idx:]
            
            engineer_assignments[engineer_id]['type_a_rides'] = assigned_rides
            engineer_assignments[engineer_id]['assigned_rides'].extend(assigned_rides)
            
            early_shifts = engineer_assignments[engineer_id]['early_shift_days']
            print(f"      {engineer_id} ({early_shifts} early shifts): {assigned_rides}")
    
    def _assign_type_bc_rides_with_coverage(self, engineer_assignments, rides, team):
        """Assign Type B/C rides with enhanced redundancy for daily PPMs"""
        print(f"\n   🎯 TYPE B/C ASSIGNMENT (enhanced redundancy for daily PPMs):")
        
        engineers_by_role = {'electrical': [], 'mechanical': []}
        for eng_id, assignment in engineer_assignments.items():
            engineers_by_role[assignment['role']].append(eng_id)
        
        # Sort engineers by early shift availability within each role  
        for role in ['electrical', 'mechanical']:
            engineers_by_role[role] = sorted(engineers_by_role[role], 
                                           key=lambda e: engineer_assignments[e]['early_shift_days'], 
                                           reverse=True)
        
        # Analyze coverage requirements for each ride
        coverage_assignments = {}
        
        for ride_id in rides:
            ride_type = self.optimizer.rides_info[ride_id]['type']
            daily_req = self.ppm_requirements[team][ride_id]['daily']
            
            # Determine minimum engineers needed for this ride
            min_elec = max(daily_req['electrical'], 1) if daily_req['electrical'] > 0 else 0
            min_mech = max(daily_req['mechanical'], 1) if daily_req['mechanical'] > 0 else 0
            
            # Enhanced redundancy for daily PPMs
            if daily_req['electrical'] > 0:
                # More redundancy for critical daily PPMs 
                if daily_req['electrical'] > 1:
                    min_elec = max(min_elec, 4)  # Maximum redundancy for critical rides
                else:
                    min_elec = max(min_elec, 3)  # Enhanced redundancy for standard daily PPMs
            if daily_req['mechanical'] > 0:
                # More redundancy for critical daily PPMs
                if daily_req['mechanical'] > 1:
                    min_mech = max(min_mech, 4)  # Maximum redundancy for critical rides  
                else:
                    min_mech = max(min_mech, 3)  # Enhanced redundancy for standard daily PPMs
            
            coverage_assignments[ride_id] = {
                'type': ride_type,
                'min_electrical': min_elec,
                'min_mechanical': min_mech,
                'daily_req_elec': daily_req['electrical'],
                'daily_req_mech': daily_req['mechanical'],
                'assigned_electrical': [],
                'assigned_mechanical': []
            }
            
            criticality = "CRITICAL" if daily_req['electrical'] > 1 or daily_req['mechanical'] > 1 else "standard"
            print(f"      {ride_id} ({ride_type}, {criticality}): needs {min_elec}E + {min_mech}M engineers")
        
        # Assign engineers to rides based on requirements (prioritize early shift engineers)
        for ride_id, requirements in coverage_assignments.items():
            # Assign electrical engineers (prioritize early shift availability)
            if requirements['min_electrical'] > 0:
                available_elec = [eng for eng in engineers_by_role['electrical'] 
                                 if len(engineer_assignments[eng]['type_b_rides'] + engineer_assignments[eng]['type_c_rides']) < 4]
                
                num_to_assign = min(requirements['min_electrical'], len(available_elec))
                # Take top early-shift engineers
                assigned_elec = available_elec[:num_to_assign]
                
                for eng_id in assigned_elec:
                    if requirements['type'] == 'B':
                        engineer_assignments[eng_id]['type_b_rides'].append(ride_id)
                    else:
                        engineer_assignments[eng_id]['type_c_rides'].append(ride_id)
                    engineer_assignments[eng_id]['assigned_rides'].append(ride_id)
                
                requirements['assigned_electrical'] = assigned_elec
                early_shifts_info = [f"{eng}({engineer_assignments[eng]['early_shift_days']})" for eng in assigned_elec]
                print(f"         Electrical: {early_shifts_info}")
            
            # Assign mechanical engineers (prioritize early shift availability)
            if requirements['min_mechanical'] > 0:
                available_mech = [eng for eng in engineers_by_role['mechanical'] 
                                 if len(engineer_assignments[eng]['type_b_rides'] + engineer_assignments[eng]['type_c_rides']) < 4]
                
                num_to_assign = min(requirements['min_mechanical'], len(available_mech))
                # Take top early-shift engineers
                assigned_mech = available_mech[:num_to_assign]
                
                for eng_id in assigned_mech:
                    if requirements['type'] == 'B':
                        engineer_assignments[eng_id]['type_b_rides'].append(ride_id)
                    else:
                        engineer_assignments[eng_id]['type_c_rides'].append(ride_id)
                    engineer_assignments[eng_id]['assigned_rides'].append(ride_id)
                
                requirements['assigned_mechanical'] = assigned_mech
                early_shifts_info = [f"{eng}({engineer_assignments[eng]['early_shift_days']})" for eng in assigned_mech]
                print(f"         Mechanical: {early_shifts_info}")
    
    def _assign_qualifications(self, engineer_assignments, team):
        """Assign qualifications with enhanced coverage ensuring all weekly PPMs are covered"""
        print(f"\n   🔧 ASSIGNING ROLE-SPECIFIC QUALIFICATIONS WITH COVERAGE CHECK:")
        
        # Track which qualifications are assigned
        assigned_qualifications = {'electrical': set(), 'mechanical': set()}
        
        # First pass: assign qualifications based on ride assignments
        for engineer_id, assignment in engineer_assignments.items():
            engineer_qualifications = []
            engineer_role = assignment['role']
            
            # Get qualifications for assigned rides, filtered by role
            for ride_id in assignment['assigned_rides']:
                for ppm_type in ['daily', 'weekly', 'monthly']:
                    if ride_id in self.optimizer.ppms_by_type[ppm_type]:
                        ppm_data = self.optimizer.ppms_by_type[ppm_type][ride_id]
                        for ppm in ppm_data['ppms']:
                            # Only assign qualifications matching engineer's role
                            if ((engineer_role == 'electrical' and ppm['maintenance_type'] == 'ELECTRICAL') or
                                (engineer_role == 'mechanical' and ppm['maintenance_type'] == 'MECHANICAL')):
                                engineer_qualifications.append(ppm['qualification_code'])
            
            # Remove duplicates and assign
            engineer_qualifications = list(set(engineer_qualifications))
            assignment['qualifications'] = engineer_qualifications
            assigned_qualifications[engineer_role].update(engineer_qualifications)
            
            print(f"      {engineer_id} ({engineer_role}): {len(engineer_qualifications)} qualifications")
        
        # Second pass: ensure all weekly and monthly qualifications are covered
        self._ensure_complete_qualification_coverage(engineer_assignments, assigned_qualifications, team)
    
    def _ensure_complete_qualification_coverage(self, engineer_assignments, assigned_qualifications, team):
        """Ensure all required qualifications are covered, especially weekly PPMs"""
        print(f"\n   🔍 ENSURING COMPLETE QUALIFICATION COVERAGE:")
        
        # Get all required qualifications for this team
        team_rides = [rid for rid, info in self.optimizer.rides_info.items() 
                     if info.get('team_responsible') == team]
        
        all_required_quals = {'electrical': set(), 'mechanical': set()}
        
        for ride_id in team_rides:
            for ppm_type in ['daily', 'weekly', 'monthly']:
                if ride_id in self.optimizer.ppms_by_type[ppm_type]:
                    ppm_data = self.optimizer.ppms_by_type[ppm_type][ride_id]
                    for ppm in ppm_data['ppms']:
                        role = 'electrical' if ppm['maintenance_type'] == 'ELECTRICAL' else 'mechanical'
                        all_required_quals[role].add(ppm['qualification_code'])
        
        # Find missing qualifications
        for role in ['electrical', 'mechanical']:
            missing_quals = all_required_quals[role] - assigned_qualifications[role]
            
            if missing_quals:
                print(f"      ⚠️  Missing {role} qualifications: {len(missing_quals)}")
                
                # Get engineers of this role sorted by early shift availability and qualification count
                role_engineers = [eng_id for eng_id, assignment in engineer_assignments.items() 
                                if assignment['role'] == role]
                role_engineers.sort(key=lambda e: (len(engineer_assignments[e]['qualifications']), 
                                                 -engineer_assignments[e]['early_shift_days']))
                
                # Distribute missing qualifications to engineers with fewest qualifications
                for qual in missing_quals:
                    # Find engineer with fewest qualifications but good early shift availability
                    best_engineer = min(role_engineers, 
                                      key=lambda e: len(engineer_assignments[e]['qualifications']))
                    
                    engineer_assignments[best_engineer]['qualifications'].append(qual)
                    assigned_qualifications[role].add(qual)
                    
                    print(f"         Added {qual} to {best_engineer}")
            else:
                print(f"      ✅ All {role} qualifications covered")
    
    def _iterative_improvement(self, engineer_assignments, team):
        """Iterative improvement based on validation feedback"""
        print(f"\n   🔄 ITERATIVE IMPROVEMENT BASED ON VALIDATION FEEDBACK:")
        
        # Create temporary matrices for validation
        temp_matrices = {team: engineer_assignments}
        
        # Run validation
        validation_results = self.coverage_validator.validate_assignment_coverage(temp_matrices)
        team_results = validation_results[team]
        
        initial_daily = team_results['daily']['coverage_percentage']
        initial_weekly = team_results['weekly']['coverage_percentage']
        
        print(f"      Initial coverage: Daily={initial_daily:.1f}%, Weekly={initial_weekly:.1f}%")
        
        # Identify specific gaps and try to fix them
        daily_gaps = team_results['daily']['coverage_gaps']
        weekly_gaps = team_results['weekly']['coverage_gaps']
        
        improvements_made = 0
        
        # Fix daily gaps by adding more engineers to critical qualifications
        if daily_gaps:
            print(f"      🔧 Fixing {len(daily_gaps)} daily coverage gaps...")
            improvements_made += self._fix_daily_gaps(engineer_assignments, daily_gaps, team)
        
        # Fix weekly gaps by ensuring qualifications are assigned
        if weekly_gaps:
            print(f"      🔧 Fixing {len(weekly_gaps)} weekly coverage gaps...")
            improvements_made += self._fix_weekly_gaps(engineer_assignments, weekly_gaps, team)
        
        # Re-validate to show improvement
        if improvements_made > 0:
            validation_results = self.coverage_validator.validate_assignment_coverage(temp_matrices)
            team_results = validation_results[team]
            
            final_daily = team_results['daily']['coverage_percentage']
            final_weekly = team_results['weekly']['coverage_percentage']
            
            print(f"      Final coverage: Daily={final_daily:.1f}% (+{final_daily-initial_daily:.1f}%), Weekly={final_weekly:.1f}% (+{final_weekly-initial_weekly:.1f}%)")
            print(f"      Applied {improvements_made} targeted improvements")
        else:
            print(f"      No additional improvements needed")
        
        return engineer_assignments
    
    def _fix_daily_gaps(self, engineer_assignments, daily_gaps, team):
        """Fix daily coverage gaps by adding more engineers to critical qualifications"""
        improvements = 0
        
        # Group gaps by ride and maintenance type
        gap_summary = defaultdict(list)
        for gap in daily_gaps:
            key = f"{gap['ride_id']}_{gap['maintenance_type']}"
            gap_summary[key].append(gap)
        
        # Fix each gap group
        for gap_key, gaps in gap_summary.items():
            ride_id, maintenance_type = gap_key.split('_')
            role = maintenance_type.lower()
            
            # Find engineers of the right role with early shifts who aren't assigned to this ride
            available_engineers = []
            for eng_id, assignment in engineer_assignments.items():
                if (assignment['role'] == role and 
                    assignment['early_shift_days'] > 0 and
                    ride_id not in assignment['assigned_rides']):
                    available_engineers.append(eng_id)
            
            # Sort by early shift availability
            available_engineers.sort(key=lambda e: engineer_assignments[e]['early_shift_days'], reverse=True)
            
            # Add the best available engineer to this ride
            if available_engineers:
                best_engineer = available_engineers[0]
                engineer_assignments[best_engineer]['assigned_rides'].append(ride_id)
                
                # Add Type B or C classification
                ride_type = self.optimizer.rides_info[ride_id]['type']
                if ride_type == 'B':
                    engineer_assignments[best_engineer]['type_b_rides'].append(ride_id)
                else:
                    engineer_assignments[best_engineer]['type_c_rides'].append(ride_id)
                
                # Add relevant qualifications for this ride
                for gap in gaps:
                    for ppm_code in gap['ppm_codes']:
                        # Find the qualification for this PPM code
                        for ppm_type in ['daily', 'weekly', 'monthly']:
                            if ride_id in self.optimizer.ppms_by_type[ppm_type]:
                                ppm_data = self.optimizer.ppms_by_type[ppm_type][ride_id]
                                for ppm in ppm_data['ppms']:
                                    if (ppm['ppm_code'] == ppm_code and 
                                        ppm['maintenance_type'] == maintenance_type.upper()):
                                        if ppm['qualification_code'] not in engineer_assignments[best_engineer]['qualifications']:
                                            engineer_assignments[best_engineer]['qualifications'].append(ppm['qualification_code'])
                
                improvements += 1
                print(f"         Added {best_engineer} to {ride_id} {maintenance_type}")
        
        return improvements
    
    def _fix_weekly_gaps(self, engineer_assignments, weekly_gaps, team):
        """Fix weekly coverage gaps by ensuring qualifications are assigned"""
        improvements = 0
        
        for gap in weekly_gaps:
            qual_code = gap['qualification_code']
            maintenance_type = gap['maintenance_type']
            role = maintenance_type.lower()
            
            # Find an engineer of the right role to assign this qualification
            role_engineers = [eng_id for eng_id, assignment in engineer_assignments.items() 
                            if assignment['role'] == role]
            
            if role_engineers:
                # Sort by early shift availability and current qualification count
                best_engineer = min(role_engineers, 
                                  key=lambda e: (len(engineer_assignments[e]['qualifications']), 
                                               -engineer_assignments[e]['early_shift_days']))
                
                if qual_code not in engineer_assignments[best_engineer]['qualifications']:
                    engineer_assignments[best_engineer]['qualifications'].append(qual_code)
                    improvements += 1
                    print(f"         Added {qual_code} to {best_engineer}")
        
        return improvements
    
    def _display_assignment_summary(self, engineer_assignments, team):
        """Display detailed assignment summary"""
        print(f"\n   📋 TEAM {team} ASSIGNMENT SUMMARY:")
        
        for engineer_id, assignment in engineer_assignments.items():
            name = assignment['name']
            role = assignment['role']
            rota = assignment['rota_number']
            
            total_rides = len(assignment['assigned_rides'])
            num_type_a = len(assignment['type_a_rides'])
            num_type_b = len(assignment['type_b_rides'])
            num_type_c = len(assignment['type_c_rides'])
            qual_count = len(assignment['qualifications'])
            
            print(f"      {engineer_id} ({name}): {role.upper()}, Rota {rota}")
            print(f"         Rides: {num_type_a}A + {num_type_b}B + {num_type_c}C = {total_rides} total")
            print(f"         Qualifications: {qual_count}")
    
    def validate_and_export_results(self, matrices):
        """Validate results using coverage validator"""
        print("\n🧪 VALIDATING RESULTS WITH COVERAGE VALIDATOR")
        print("=" * 70)
        
        # Run coverage validation
        validation_results = self.coverage_validator.validate_assignment_coverage(matrices)
        
        # Note: Export is now handled by StandardOutputManager in the main script
        
        return validation_results


def main():
    """Run coverage-optimized qualification design"""
    # This would typically be called with PPM data
    print("Coverage-Optimized Qualification Designer")
    print("Requires PPM data to be loaded first")


if __name__ == "__main__":
    main() 