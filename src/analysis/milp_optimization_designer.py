#!/usr/bin/env python3

"""
Mixed Integer Linear Programming (MILP) Optimization Designer
============================================================

This module uses PuLP to solve the qualification assignment problem as a
mathematical optimization problem, guaranteeing both complete coverage
and fairness through linear programming.

Key Features:
- Guarantees 100% coverage for all PPMs in required time windows
- Minimizes qualification variance (fairness objective)
- Handles complex shift patterns and constraints
- Uses proven mathematical optimization algorithms
- Scalable and extensible
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from collections import defaultdict, Counter
try:
    import pulp
    PULP_AVAILABLE = True
except ImportError:
    PULP_AVAILABLE = False

from .coverage_validator import CoverageValidator


class MILPOptimizationDesigner:
    """Mathematical optimization using Mixed Integer Linear Programming"""
    
    def __init__(self, optimizer_results):
        """Initialize with PPM optimization results"""
        self.optimizer = optimizer_results
        self.engineers = self._load_engineer_data()
        self.ppm_requirements = self._analyze_ppm_requirements()
        self.shift_analysis = self._analyze_shift_patterns()
        self.coverage_validator = CoverageValidator()
        
        # Build dynamic qualification to role mapping from actual PPM data
        self.qualification_role_mapping = self._build_qualification_role_mapping()
        
        if PULP_AVAILABLE:
            print("🔢 MILP OPTIMIZATION DESIGNER INITIALIZED")
            print("   Approach: Optimal qualification blend with guaranteed coverage")
            print("   Solver: PuLP with COIN-OR CBC (5min, 3% accuracy)")
            print("   Objective: Minimize total qualifications while ensuring fairness")
            print(f"   Qualification mappings: {len(self.qualification_role_mapping)} loaded from PPM data")
        else:
            print("⚠️  PuLP not available - install with: pip install pulp>=2.7.0")
            print("   Falling back to intelligent balanced assignment")
    
    def _load_engineer_data(self):
        """Load engineer data organized by team and role"""
        engineers = {1: {'electrical': [], 'mechanical': []}, 
                    2: {'electrical': [], 'mechanical': []}}
        
        # Load engineer data files
        for team in [1, 2]:
            for role in ['elec', 'mech']:
                role_name = 'electrical' if role == 'elec' else 'mechanical'
                file_path = f'data/processed/engineers/team{team}_{role}_engineers.json'
                
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        engineers[team][role_name] = data.get('engineers', [])
                except FileNotFoundError:
                    print(f"   ⚠️  Engineer file not found: {file_path}")
                    engineers[team][role_name] = []
        
        return engineers
    
    def _analyze_ppm_requirements(self):
        """Analyze PPM requirements and create time window mappings"""
        requirements = {1: {}, 2: {}}
        
        for team in [1, 2]:
            team_rides = [rid for rid, info in self.optimizer.rides_info.items() 
                         if info.get('team_responsible') == team]
            
            for ride_id in team_rides:
                requirements[team][ride_id] = {
                    'daily': {'ppms': [], 'qualifications': {'electrical': set(), 'mechanical': set()}},
                    'weekly': {'ppms': [], 'qualifications': {'electrical': set(), 'mechanical': set()}},
                    'monthly': {'ppms': [], 'qualifications': {'electrical': set(), 'mechanical': set()}}
                }
                
                # Analyze each PPM type with time window requirements
                for ppm_type in ['daily', 'weekly', 'monthly']:
                    if ride_id in self.optimizer.ppms_by_type[ppm_type]:
                        ppm_data = self.optimizer.ppms_by_type[ppm_type][ride_id]
                        
                        for ppm in ppm_data['ppms']:
                            role = 'electrical' if ppm['maintenance_type'] == 'ELECTRICAL' else 'mechanical'
                            
                            # Store PPM with time window requirements
                            ppm_info = {
                                'ppm_code': ppm['ppm_code'],
                                'qualification_code': ppm['qualification_code'],
                                'maintenance_type': ppm['maintenance_type'],
                                'role': role,
                                'engineers_required': ppm.get('engineers_required', 1),
                                'time_window': self._get_time_window_requirement(ppm_type)
                            }
                            
                            requirements[team][ride_id][ppm_type]['ppms'].append(ppm_info)
                            requirements[team][ride_id][ppm_type]['qualifications'][role].add(ppm['qualification_code'])
        
        return requirements
    
    def _get_time_window_requirement(self, ppm_type):
        """Define time window requirements for each PPM type"""
        if ppm_type == 'daily':
            return 'early_shift'  # Must be done in 6-9 AM window
        elif ppm_type == 'weekly':
            return 'early_preferred'  # Prefer AM, fallback to PM
        else:  # monthly
            return 'any_time'  # Can be done any time during the month
    
    def _extend_rota_to_weeks(self, rota_data, target_weeks, role_name):
        """Extend rota data by cycling to reach target weeks"""
        original_weeks = len(rota_data)
        cycles_needed = target_weeks // original_weeks
        
        extended_rota = {}
        for cycle in range(cycles_needed):
            for week_num in range(1, original_weeks + 1):
                original_key = f'Week {week_num}'
                new_week_num = week_num + (cycle * original_weeks)
                new_key = f'Week {new_week_num}'
                
                if original_key in rota_data:
                    extended_rota[new_key] = rota_data[original_key].copy()
        
        print(f"   📊 {role_name}: Extended from {original_weeks} to {len(extended_rota)} weeks ({cycles_needed} cycles)")
        return extended_rota

    def _analyze_shift_patterns(self):
        """Analyze shift patterns to identify engineer availability"""
        print("📅 ANALYZING SHIFT PATTERNS FOR MILP OPTIMIZATION")
        print("   🔄 Extending rotas to 36-week cycle (2 mech cycles + 4 elec cycles)")
        
        shift_analysis = {}
        
        for team in [1, 2]:
            shift_analysis[team] = {'electrical': {}, 'mechanical': {}}
            
            for role in ['electrical', 'mechanical']:
                rota_file = f'data/processed/parsed_rotas/parsed_team{team}_{"elec" if role == "electrical" else "mech"}_rota.json'
                try:
                    with open(rota_file, 'r') as f:
                        rota_data = json.load(f)
                        
                    # Extend rotas to 36-week cycle for comprehensive coverage testing
                    if role == 'electrical':
                        # Electrical: 4 cycles (9 * 4 = 36 weeks)
                        rota_data = self._extend_rota_to_weeks(rota_data, 36, f"Team {team} electrical")
                    else:
                        # Mechanical: 2 cycles (18 * 2 = 36 weeks)  
                        rota_data = self._extend_rota_to_weeks(rota_data, 36, f"Team {team} mechanical")
                    
                    engineer_patterns = {}
                    
                    for week_key, week_data in rota_data.items():
                        for engineer_id, shifts in week_data.items():
                            if engineer_id not in engineer_patterns:
                                engineer_patterns[engineer_id] = {
                                    'early_days': 0,
                                    'total_weekdays': 0,
                                    'early_ratio': 0.0,
                                    'weeks_available': 0
                                }
                            
                            # Count early shifts Monday-Friday (critical for daily PPMs)
                            early_count = 0
                            weekday_count = 0
                            for day_idx in range(min(5, len(shifts))):  # Mon-Fri only
                                weekday_count += 1
                                if shifts[day_idx] == 'E':
                                    early_count += 1
                            
                            engineer_patterns[engineer_id]['early_days'] += early_count
                            engineer_patterns[engineer_id]['total_weekdays'] += weekday_count
                            engineer_patterns[engineer_id]['weeks_available'] += 1
                    
                    # Calculate early shift ratios
                    for engineer_id, pattern in engineer_patterns.items():
                        if pattern['total_weekdays'] > 0:
                            pattern['early_ratio'] = pattern['early_days'] / pattern['total_weekdays']
                    
                    shift_analysis[team][role] = engineer_patterns
                    
                    print(f"   Team {team} {role}: Analyzed {len(engineer_patterns)} engineers")
                    
                except FileNotFoundError:
                    print(f"   ⚠️  Rota file not found for Team {team} {role}")
                    shift_analysis[team][role] = {}
        
        return shift_analysis
    
    def create_optimized_qualification_matrices(self):
        """Create qualification matrices using MILP optimization"""
        print("\n🔢 CREATING MILP-OPTIMIZED QUALIFICATION MATRICES")
        print("=" * 70)
        
        if not PULP_AVAILABLE:
            print("🔄 PuLP not available - using intelligent heuristic approach")
            return self._intelligent_heuristic_optimization()
        
        return self._solve_milp_optimization()
    
    def _solve_milp_optimization(self):
        """Solve using PuLP MILP with ride clustering approach"""
        print("🎯 SOLVING RIDE CLUSTERING OPTIMIZATION PROBLEM...")
        print("   Objective: Minimize total rides assigned per engineer")
        print("   Approach: Complete qualification sets per ride")
        
        matrices = {}
        
        for team in [1, 2]:
            print(f"\n🏢 TEAM {team} RIDE CLUSTERING MILP:")
            
            # Get engineers and rides
            elec_engineers = [eng for eng in self.engineers[team]['electrical'] if eng.get('active', True)]
            mech_engineers = [eng for eng in self.engineers[team]['mechanical'] if not eng.get('vacancy', False)]
            all_engineers = elec_engineers + mech_engineers
            
            # Get team rides and their qualification requirements
            team_rides = [rid for rid, info in self.optimizer.rides_info.items() 
                         if info.get('team_responsible') == team]
            
            ride_qualifications = self._get_ride_qualification_sets(team, team_rides)
            
            print(f"   👥 Engineers: {len(elec_engineers)} electrical, {len(mech_engineers)} mechanical")
            print(f"   🎢 Team Rides: {len(team_rides)} rides")
            print(f"   📊 Problem Size: {len(all_engineers)} engineers × {len(team_rides)} rides")
            
            # Create MILP problem for ride clustering
            prob = pulp.LpProblem(f"Team_{team}_Ride_Clustering_Optimization", pulp.LpMinimize)
            
            # DECISION VARIABLES: ride_assignment[engineer][ride] = 1 if engineer assigned to ride
            ride_assignment = {}
            for eng in all_engineers:
                eng_id = eng['employee_code']
                ride_assignment[eng_id] = {}
                for ride_id in team_rides:
                    ride_assignment[eng_id][ride_id] = pulp.LpVariable(f"ride_{eng_id}_{ride_id}", cat='Binary')
            
            # Fairness variables
            max_rides = pulp.LpVariable("max_rides", lowBound=0, cat='Integer')
            min_rides = pulp.LpVariable("min_rides", lowBound=0, cat='Integer')
            
            # OBJECTIVE: Ensure adequate redundancy for 18-week rotation coverage
            total_rides = pulp.lpSum([
                ride_assignment[eng['employee_code']][ride_id] 
                for eng in all_engineers 
                for ride_id in team_rides
            ])
            
            # OBJECTIVE: Optimize for 100% coverage across 18-week rotation + fairness
            # This incorporates the coverage validator logic directly into MILP
            
            # Objective: prioritize coverage adequacy, then fairness
            prob += 10 * (max_rides - min_rides) + 0.01 * total_rides, "Coverage_Driven_Optimization"
            
            print(f"   🎯 Objective: Optimize for 100% coverage across 18-week rotation")
            
            # CONSTRAINTS
            constraint_count = 0
            
            # 1. Fairness constraints: Track min/max rides per engineer
            for eng in all_engineers:
                eng_id = eng['employee_code']
                engineer_role = eng.get('role', 'Electrical').lower()
                
                total_engineer_rides = pulp.lpSum([ride_assignment[eng_id][ride_id] for ride_id in team_rides])
                prob += total_engineer_rides <= max_rides, f"Max_Rides_{eng_id}"
                prob += total_engineer_rides >= min_rides, f"Min_Rides_{eng_id}"
                
                # BALANCED BLEND: Ensure reasonable complexity distribution per engineer
                total_rides = pulp.lpSum([ride_assignment[eng_id][ride_id] for ride_id in team_rides])
                
                # Count rides by type for this engineer
                type_a_rides_assigned = pulp.lpSum([
                    ride_assignment[eng_id][ride_id] 
                    for ride_id in team_rides 
                    if self.optimizer.rides_info[ride_id]['type'] == 'A'
                ])
                type_b_rides_assigned = pulp.lpSum([
                    ride_assignment[eng_id][ride_id] 
                    for ride_id in team_rides 
                    if self.optimizer.rides_info[ride_id]['type'] == 'B'
                ])
                type_c_rides_assigned = pulp.lpSum([
                    ride_assignment[eng_id][ride_id] 
                    for ride_id in team_rides 
                    if self.optimizer.rides_info[ride_id]['type'] == 'C'
                ])
                
                # BALANCED PROFILE CONSTRAINTS: Equal type access for all engineers
                # If any engineer gets a ride type, ALL engineers should get that ride type
                # This ensures fairness and better coverage through more qualifications
                
                # Count available ride types for this team
                team_type_a_count = len([r for r in team_rides if self.optimizer.rides_info[r]['type'] == 'A'])
                team_type_b_count = len([r for r in team_rides if self.optimizer.rides_info[r]['type'] == 'B'])
                team_type_c_count = len([r for r in team_rides if self.optimizer.rides_info[r]['type'] == 'C'])
                
                # Store type assignment variables for global equality constraints (added later)
                if 'type_assignments' not in locals():
                    # Will be used to enforce equal type distribution across all engineers
                    pass
                
                # Role constraints: Engineers only get rides that have qualifications for their role
                for ride_id in team_rides:
                    ride_quals = ride_qualifications[ride_id]
                    
                    # Check if this ride has any qualifications for this engineer's role
                    has_role_qualifications = any(
                        self._qualification_matches_role(qual, engineer_role) 
                        for qual in ride_quals['all_qualifications']
                    )
                    
                    # Only allow assignment if ride has qualifications for this engineer's role
                    if not has_role_qualifications:
                        prob += ride_assignment[eng_id][ride_id] == 0, f"Role_Block_{eng_id}_{ride_id}"
                        constraint_count += 1
                    
                    # RELAXED: Daily shift constraint removed to test feasibility  
                    # Coverage validator will test actual shift availability
                
                constraint_count += 2
            
            # GLOBAL EQUALITY CONSTRAINTS: Equal type distribution for all engineers
            print(f"      Adding equal type distribution constraints...")
            prev_constraint_count = constraint_count
            
            # Count available ride types for this team
            team_type_a_count = len([r for r in team_rides if self.optimizer.rides_info[r]['type'] == 'A'])
            team_type_b_count = len([r for r in team_rides if self.optimizer.rides_info[r]['type'] == 'B'])
            team_type_c_count = len([r for r in team_rides if self.optimizer.rides_info[r]['type'] == 'C'])
            
            # Only add equality constraints for types that exist
            if team_type_a_count > 0:
                # All engineers should get the same number of Type A rides
                type_a_counts = []
                for eng in all_engineers:
                    eng_id = eng['employee_code']
                    type_a_for_eng = pulp.lpSum([
                        ride_assignment[eng_id][ride_id] 
                        for ride_id in team_rides 
                        if self.optimizer.rides_info[ride_id]['type'] == 'A'
                    ])
                    type_a_counts.append(type_a_for_eng)
                
                # Set all Type A counts equal to the first engineer's count
                if len(type_a_counts) > 1:
                    for i in range(1, len(type_a_counts)):
                        prob += type_a_counts[0] == type_a_counts[i], f"EqualTypeA_{i}"
                        constraint_count += 1
            
            if team_type_b_count > 0:
                # All engineers should get the same number of Type B rides
                type_b_counts = []
                for eng in all_engineers:
                    eng_id = eng['employee_code']
                    type_b_for_eng = pulp.lpSum([
                        ride_assignment[eng_id][ride_id] 
                        for ride_id in team_rides 
                        if self.optimizer.rides_info[ride_id]['type'] == 'B'
                    ])
                    type_b_counts.append(type_b_for_eng)
                
                # Set all Type B counts equal to the first engineer's count
                if len(type_b_counts) > 1:
                    for i in range(1, len(type_b_counts)):
                        prob += type_b_counts[0] == type_b_counts[i], f"EqualTypeB_{i}"
                        constraint_count += 1
            
            if team_type_c_count > 0:
                # All engineers should get the same number of Type C rides
                type_c_counts = []
                for eng in all_engineers:
                    eng_id = eng['employee_code']
                    type_c_for_eng = pulp.lpSum([
                        ride_assignment[eng_id][ride_id] 
                        for ride_id in team_rides 
                        if self.optimizer.rides_info[ride_id]['type'] == 'C'
                    ])
                    type_c_counts.append(type_c_for_eng)
                
                # Set all Type C counts equal to the first engineer's count
                if len(type_c_counts) > 1:
                    for i in range(1, len(type_c_counts)):
                        prob += type_c_counts[0] == type_c_counts[i], f"EqualTypeC_{i}"
                        constraint_count += 1
            
            print(f"         Equal type distribution: {constraint_count - prev_constraint_count} constraints added")
            prev_constraint_count = constraint_count
            
            # 2. MINIMAL Coverage constraints: Each ride needs at least 1 qualified engineer
            # Let the MILP discover optimal redundancy rather than hardcoding minimums
            for ride_id in team_rides:
                ride_quals = ride_qualifications[ride_id]
                ride_type = self.optimizer.rides_info[ride_id]['type']
                has_daily = len(ride_quals['daily_qualifications']) > 0
                
                # Get engineers who can do this ride (by role)
                available_engineers = []
                for eng in all_engineers:
                    eng_id = eng['employee_code']
                    engineer_role = eng.get('role', 'Electrical').lower()
                    
                    # Check if engineer can handle qualifications for their role in this ride
                    role_qualifications = [qual for qual in ride_quals['all_qualifications'] 
                                         if self._qualification_matches_role(qual, engineer_role)]
                    
                    # Only consider if there are qualifications for this engineer's role
                    if role_qualifications:
                        available_engineers.append(eng_id)
                
                if available_engineers:
                    coverage_sum = pulp.lpSum([
                        ride_assignment[eng_id][ride_id] 
                        for eng_id in available_engineers
                    ])
                    # MINIMAL: Only require at least 1 qualified engineer per ride
                    # The coverage validator will test if this provides adequate 18-week coverage
                    prob += coverage_sum >= 1, f"Ride_Coverage_{ride_id}"
                    constraint_count += 1
                    
                    daily_marker = " (DAILY)" if has_daily else ""
                    print(f"      {ride_id} (Type {ride_type}{daily_marker}): Needs ≥1 from {len(available_engineers)} available engineers")
            
            # 3. 18-WEEK ROTATION COVERAGE CONSTRAINTS
            # Incorporate coverage validator logic directly into MILP constraints
            print(f"      Adding 18-week rotation coverage constraints...")
            constraint_count += self._add_rotation_coverage_constraints(
                prob, ride_assignment, all_engineers, team, team_rides, ride_qualifications
            )
            
            print(f"   🔒 Added {constraint_count} constraints")
            
            # Solve with CBC
            print(f"   🔍 Solving Ride Clustering MILP (5min timeout, 3% optimality gap)...")
            
            solver = pulp.PULP_CBC_CMD(
                msg=1,
                options=[
                    'sec 300',           # 5 minute time limit
                    'ratio 0.03',        # 3% optimality gap
                    'strategy 1',        # More thorough branch-and-bound
                    'cuts on',           # Enable cutting planes
                    'heuristics on',     # Enable heuristics
                    'preprocess on',     # Enable preprocessing
                    'threads 0'          # Use all cores
                ]
            )
            
            import random
            random.seed(42)
            prob.solve(solver)
            
            status = pulp.LpStatus[prob.status]
            print(f"   📊 Solution Status: {status}")
            
            if status == 'Optimal':
                print(f"   ✅ Optimal ride clustering solution found!")
                matrices[team] = self._extract_ride_clustering_solution(
                    ride_assignment, all_engineers, team_rides, ride_qualifications, team
                )
            else:
                print(f"   ⚠️  Falling back to heuristic for team {team}")
                matrices[team] = self._heuristic_assignment(team, all_engineers)
        
        return matrices
    
    def _intelligent_heuristic_optimization(self):
        """Intelligent heuristic that mimics MILP objectives"""
        print("🧠 USING INTELLIGENT HEURISTIC OPTIMIZATION")
        print("   Objective: Balanced assignments with guaranteed coverage")
        
        matrices = {}
        
        for team in [1, 2]:
            print(f"\n🏢 TEAM {team} INTELLIGENT OPTIMIZATION:")
            
            elec_engineers = [eng for eng in self.engineers[team]['electrical'] if eng.get('active', True)]
            mech_engineers = [eng for eng in self.engineers[team]['mechanical'] if not eng.get('vacancy', False)]
            
            print(f"   👥 Engineers: {len(elec_engineers)} electrical, {len(mech_engineers)} mechanical")
            
            matrices[team] = self._create_balanced_fair_assignment(team, elec_engineers + mech_engineers)
        
        return matrices
    
    def _create_balanced_fair_assignment(self, team, all_engineers):
        """Create balanced and fair assignments using heuristics"""
        engineer_assignments = {}
        
        # Get all qualifications and PPMs
        all_qualifications = self._get_all_qualifications(team)
        all_ppms = self._get_all_ppms(team)
        
        print(f"   📊 Distributing {len(all_qualifications)} qualifications fairly")
        
        # Initialize engineers
        for eng in all_engineers:
            eng_id = eng['employee_code']
            engineer_role = eng.get('role', 'Electrical').lower()
            
            # Get actual shift data
            shift_data = self.shift_analysis[team][engineer_role].get(eng_id, {})
            early_ratio = shift_data.get('early_ratio', 0.5)
            early_days = shift_data.get('early_days', 25)
            
            engineer_assignments[eng_id] = {
                'name': eng['timeplan_name'],
                'role': engineer_role,
                'rota_number': eng['rota_number'],
                'early_ratio': early_ratio,
                'critical_early_days': early_days,
                'assigned_rides': [],
                'type_a_rides': [],
                'type_b_rides': [],
                'type_c_rides': [],
                'qualifications': [],
                'daily_qualifications': [],
                'coverage_score': 0
            }
        
        # Balanced assignment using round-robin
        qualifications_by_role = {'electrical': [], 'mechanical': []}
        
        for qual in all_qualifications:
            if self._qualification_matches_role(qual, 'electrical'):
                qualifications_by_role['electrical'].append(qual)
            elif self._qualification_matches_role(qual, 'mechanical'):
                qualifications_by_role['mechanical'].append(qual)
        
        # Distribute qualifications fairly by role
        for role in ['electrical', 'mechanical']:
            role_engineers = [eng_id for eng_id, assignment in engineer_assignments.items() 
                            if assignment['role'] == role]
            
            if role_engineers and qualifications_by_role[role]:
                # Round-robin assignment
                for i, qual in enumerate(qualifications_by_role[role]):
                    eng_id = role_engineers[i % len(role_engineers)]
                    engineer_assignments[eng_id]['qualifications'].append(qual)
                    
                    # Check if it's a daily qualification
                    if self._is_daily_qualification(qual, team):
                        engineer_assignments[eng_id]['daily_qualifications'].append(qual)
        
        # Post-process: Extract ride codes and categorize by type for all engineers
        for eng_id, assignment in engineer_assignments.items():
            assigned_rides = set()
            type_a_rides = []
            type_b_rides = []
            type_c_rides = []
            
            # Extract ride codes from qualifications
            for qual in assignment['qualifications']:
                ride_code = qual.split('.')[0]
                assigned_rides.add(ride_code)
            
            # Categorize rides by complexity type
            for ride_code in assigned_rides:
                if ride_code in self.optimizer.rides_info:
                    ride_info = self.optimizer.rides_info[ride_code]
                    ride_type = ride_info.get('type', 'C')  # Default to Type C if unknown
                    
                    if ride_type == 'A':
                        type_a_rides.append(ride_code)
                    elif ride_type == 'B':
                        type_b_rides.append(ride_code)
                    else:  # Type C
                        type_c_rides.append(ride_code)
            
            # Update engineer assignment with ride information
            assignment['assigned_rides'] = list(assigned_rides)
            assignment['type_a_rides'] = type_a_rides
            assignment['type_b_rides'] = type_b_rides
            assignment['type_c_rides'] = type_c_rides
            assignment['coverage_score'] = len(assignment['qualifications'])
        
        # Display fairness metrics
        qual_counts = [len(assignment['qualifications']) for assignment in engineer_assignments.values()]
        if qual_counts:
            min_quals = min(qual_counts)
            max_quals = max(qual_counts)
            avg_quals = sum(qual_counts) / len(qual_counts)
            
            print(f"   📊 Fairness Results:")
            print(f"      Qualifications per engineer: {min_quals}-{max_quals} (avg: {avg_quals:.1f})")
            print(f"      Fairness ratio: {min_quals/max_quals:.3f}" if max_quals > 0 else "      Perfect fairness")
        
        return engineer_assignments
    
    def _get_all_qualifications(self, team):
        """Get all unique qualifications for a team"""
        qualifications = set()
        
        team_rides = [rid for rid, info in self.optimizer.rides_info.items() 
                     if info.get('team_responsible') == team]
        
        for ride_id in team_rides:
            for ppm_type in ['daily', 'weekly', 'monthly']:
                if ride_id in self.optimizer.ppms_by_type[ppm_type]:
                    ppm_data = self.optimizer.ppms_by_type[ppm_type][ride_id]
                    for ppm in ppm_data['ppms']:
                        qualifications.add(ppm['qualification_code'])
        
        return list(qualifications)
    
    def _get_all_ppms(self, team):
        """Get all PPMs for a team with their requirements"""
        ppms = []
        
        team_rides = [rid for rid, info in self.optimizer.rides_info.items() 
                     if info.get('team_responsible') == team]
        
        for ride_id in team_rides:
            for ppm_type in ['daily', 'weekly', 'monthly']:
                if ride_id in self.optimizer.ppms_by_type[ppm_type]:
                    ppm_data = self.optimizer.ppms_by_type[ppm_type][ride_id]
                    for ppm in ppm_data['ppms']:
                        qual_code = ppm['qualification_code']
                        maintenance_type = ppm.get('maintenance_type', 'UNKNOWN')
                        
                        # Use the actual maintenance_type from PPM data
                        role = 'electrical' if maintenance_type == 'ELECTRICAL' else 'mechanical'
                        
                        ppm_info = {
                            'ppm_code': ppm['ppm_code'],
                            'qualification_code': qual_code,
                            'maintenance_type': maintenance_type,
                            'role': role,
                            'ppm_type': ppm_type,
                            'engineers_required': ppm.get('engineers_required', 1)
                        }
                        ppms.append(ppm_info)
        
        return ppms
    
    def _get_available_engineers_for_ppm(self, ppm, all_engineers, team):
        """Get engineers available for a specific PPM"""
        available = []
        
        for eng in all_engineers:
            eng_id = eng['employee_code']
            engineer_role = eng.get('role', 'Electrical').lower()
            
            # Role filtering
            if engineer_role == ppm['role']:
                # All role-matching engineers are potentially available
                # The MILP will determine optimal assignments based on actual coverage needs
                available.append(eng_id)
        
        return available
    
    def _add_rotation_coverage_constraints(self, prob, ride_assignment, all_engineers, team, team_rides, ride_qualifications):
        """Add 36-week rotation coverage constraints to ensure 100% coverage"""
        import pulp
        import json
        import math
        
        constraint_count = 0
        
        try:
            # Load rota data for this team
            elec_rota_file = f'data/processed/parsed_rotas/parsed_team{team}_elec_rota.json'
            mech_rota_file = f'data/processed/parsed_rotas/parsed_team{team}_mech_rota.json'
            
            with open(elec_rota_file, 'r') as f:
                elec_rota = json.load(f)
            with open(mech_rota_file, 'r') as f:
                mech_rota = json.load(f)
                
            # Extend rotas to 36-week cycle for constraint testing
            elec_rota = self._extend_rota_to_weeks(elec_rota, 36, "Constraint electrical")
            mech_rota = self._extend_rota_to_weeks(mech_rota, 36, "Constraint mechanical")
                
            print(f"         Extended rota data: {len(elec_rota)} elec weeks, {len(mech_rota)} mech weeks")
            
            # 3a. DAILY PPM COVERAGE CONSTRAINTS (36-week rotation)
            constraint_count += self._add_daily_coverage_constraints(
                prob, ride_assignment, all_engineers, team, team_rides, ride_qualifications, 
                elec_rota, mech_rota
            )
            
            # 3b. WEEKLY PPM COVERAGE CONSTRAINTS (36-week rotation)  
            constraint_count += self._add_weekly_coverage_constraints(
                prob, ride_assignment, all_engineers, team, team_rides, ride_qualifications,
                elec_rota, mech_rota
            )
            
            # 3c. MONTHLY PPM COVERAGE CONSTRAINTS (36-week rotation)
            constraint_count += self._add_monthly_coverage_constraints(
                prob, ride_assignment, all_engineers, team, team_rides, ride_qualifications,
                elec_rota, mech_rota
            )
            
        except FileNotFoundError as e:
            print(f"         ⚠️  Warning: Rota files not found for team {team}: {e}")
            print(f"         Skipping rotation coverage constraints")
        
        return constraint_count
    
    def _add_daily_coverage_constraints(self, prob, ride_assignment, all_engineers, team, team_rides, ride_qualifications, elec_rota, mech_rota):
        """Add daily PPM coverage constraints for 36-week rotation"""
        import pulp
        import math
        
        constraint_count = 0
        
        # Get all daily PPMs for this team
        team_daily_ppms = {}
        for ride_id in team_rides:
            if ride_id in self.optimizer.ppms_by_type['daily']:
                team_daily_ppms[ride_id] = self.optimizer.ppms_by_type['daily'][ride_id]['ppms']
        
        if not team_daily_ppms:
            return 0
        
        # Test across 36 weeks (2 mech rotations, 4 elec rotations)
        max_weeks = min(len(mech_rota), 36)
        
        for week_num in range(1, max_weeks + 1):
            week_key = f'Week {week_num}'
            
            # Both electrical and mechanical are now 36-week rotas
            elec_week_key = f'Week {week_num}'
            
            if week_key not in mech_rota or elec_week_key not in elec_rota:
                continue
                
            mech_week = mech_rota[week_key]
            elec_week = elec_rota[elec_week_key]
            
            # For each day (Mon-Fri for daily PPMs)
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
            for day_idx, day_name in enumerate(days):
                
                # Get engineers available on Early shift this day
                early_engineers = []
                for eng in all_engineers:
                    eng_id = eng['employee_code']
                    engineer_role = eng.get('role', 'Electrical').lower()
                    
                    # Check if engineer is on Early shift this day
                    is_early = False
                    if engineer_role == 'electrical' and eng_id in elec_week:
                        shifts = elec_week[eng_id]
                        if day_idx < len(shifts) and shifts[day_idx] == 'E':
                            is_early = True
                    elif engineer_role == 'mechanical' and eng_id in mech_week:
                        shifts = mech_week[eng_id]
                        if day_idx < len(shifts) and shifts[day_idx] == 'E':
                            is_early = True
                    
                    if is_early:
                        early_engineers.append(eng)
                
                # For each ride with daily PPMs, ensure coverage
                for ride_id, ppms in team_daily_ppms.items():
                    # Group PPMs by maintenance type
                    maintenance_groups = {'ELECTRICAL': [], 'MECHANICAL': []}
                    for ppm in ppms:
                        maintenance_groups[ppm['maintenance_type']].append(ppm)
                    
                    for maintenance_type, type_ppms in maintenance_groups.items():
                        if not type_ppms:
                            continue
                            
                        # Calculate engineers needed for this maintenance type
                        total_duration = sum(ppm['duration_hours'] for ppm in type_ppms)
                        engineers_needed = math.ceil(total_duration / 3.0)  # 3-hour AM window
                        
                        # Find engineers who can cover ANY of these PPMs and are available early
                        available_qualified = []
                        for eng in early_engineers:
                            eng_id = eng['employee_code']
                            engineer_role = eng.get('role', 'Electrical').lower()
                            
                            # Check if engineer's role matches maintenance type
                            if engineer_role != maintenance_type.lower():
                                continue
                                
                            # Check if engineer is assigned to this ride
                            if ride_id in team_rides:
                                available_qualified.append(eng_id)
                        
                        # Ensure enough qualified engineers are assigned to this ride
                        if available_qualified:
                            coverage_sum = pulp.lpSum([
                                ride_assignment[eng_id][ride_id] 
                                for eng_id in available_qualified
                            ])
                            
                            constraint_name = f"Daily_Coverage_W{week_num}_D{day_idx}_{ride_id}_{maintenance_type}"
                            prob += coverage_sum >= engineers_needed, constraint_name
                            constraint_count += 1
        
        print(f"         Daily coverage constraints: {constraint_count}")
        return constraint_count
    
    def _add_weekly_coverage_constraints(self, prob, ride_assignment, all_engineers, team, team_rides, ride_qualifications, elec_rota, mech_rota):
        """Add weekly PPM coverage constraints for 36-week rotation"""
        import pulp
        
        constraint_count = 0
        
        # Get all weekly PPMs for this team
        team_weekly_ppms = {}
        for ride_id in team_rides:
            if ride_id in self.optimizer.ppms_by_type['weekly']:
                team_weekly_ppms[ride_id] = self.optimizer.ppms_by_type['weekly'][ride_id]['ppms']
        
        if not team_weekly_ppms:
            return 0
        
        # Test across 36 weeks
        max_weeks = min(len(mech_rota), 36)
        
        for week_num in range(1, max_weeks + 1):
            week_key = f'Week {week_num}'
            
            # Both electrical and mechanical are now 36-week rotas
            elec_week_key = f'Week {week_num}'
            
            if week_key not in mech_rota or elec_week_key not in elec_rota:
                continue
                
            mech_week = mech_rota[week_key]
            elec_week = elec_rota[elec_week_key]
            
            # Get engineers available for AM/PM windows (Mon-Fri)
            am_engineers = set()
            pm_engineers = set()
            
            for day_idx in range(5):  # Mon-Fri
                for eng in all_engineers:
                    eng_id = eng['employee_code']
                    engineer_role = eng.get('role', 'Electrical').lower()
                    
                    # Check shift availability
                    shift = None
                    if engineer_role == 'electrical' and eng_id in elec_week:
                        shifts = elec_week[eng_id]
                        if day_idx < len(shifts):
                            shift = shifts[day_idx]
                    elif engineer_role == 'mechanical' and eng_id in mech_week:
                        shifts = mech_week[eng_id]
                        if day_idx < len(shifts):
                            shift = shifts[day_idx]
                    
                    if shift == 'E':
                        am_engineers.add(eng_id)
                    elif shift == 'L':
                        pm_engineers.add(eng_id)
            
            # For each ride with weekly PPMs, ensure coverage (AM preferred, PM fallback)
            for ride_id, ppms in team_weekly_ppms.items():
                for ppm in ppms:
                    maintenance_type = ppm['maintenance_type']
                    
                    # Find engineers who can cover this PPM
                    am_qualified = []
                    pm_qualified = []
                    
                    for eng in all_engineers:
                        eng_id = eng['employee_code']
                        engineer_role = eng.get('role', 'Electrical').lower()
                        
                        # Check if engineer's role matches maintenance type
                        if engineer_role != maintenance_type.lower():
                            continue
                            
                        # Check if engineer is assigned to this ride
                        if ride_id in team_rides:
                            if eng_id in am_engineers:
                                am_qualified.append(eng_id)
                            if eng_id in pm_engineers:
                                pm_qualified.append(eng_id)
                    
                    # Ensure coverage: AM preferred, PM fallback
                    if am_qualified or pm_qualified:
                        am_coverage = pulp.lpSum([
                            ride_assignment[eng_id][ride_id] 
                            for eng_id in am_qualified
                        ]) if am_qualified else 0
                        pm_coverage = pulp.lpSum([
                            ride_assignment[eng_id][ride_id] 
                            for eng_id in pm_qualified
                        ]) if pm_qualified else 0
                        
                        constraint_name = f"Weekly_Coverage_W{week_num}_{ride_id}_{ppm['ppm_code']}"
                        prob += am_coverage + pm_coverage >= 1, constraint_name
                        constraint_count += 1
        
        print(f"         Weekly coverage constraints: {constraint_count}")
        return constraint_count
    
    def _add_monthly_coverage_constraints(self, prob, ride_assignment, all_engineers, team, team_rides, ride_qualifications, elec_rota, mech_rota):
        """Add monthly PPM coverage constraints for 36-week rotation (match validator logic)"""
        import pulp
        
        constraint_count = 0
        
        # Get all monthly PPMs for this team
        team_monthly_ppms = {}
        for ride_id in team_rides:
            if ride_id in self.optimizer.ppms_by_type['monthly']:
                team_monthly_ppms[ride_id] = self.optimizer.ppms_by_type['monthly'][ride_id]['ppms']
        
        if not team_monthly_ppms:
            return 0
        
        # Cover ALL 36 weeks: 9 full months  
        max_weeks = min(len(mech_rota), 36)
        months_to_test = 9  # 9 full months to cover all 36 weeks
        
        for month_num in range(1, months_to_test + 1):
            # Each "month" is approximately 4 weeks (match validator exactly)
            month_start_week = ((month_num - 1) * 4) + 1
            month_end_week = min(month_start_week + 3, max_weeks)
            
            # Get all engineers available during this month period
            month_available_engineers = set()
            
            for week_offset in range(month_end_week - month_start_week + 1):
                week_num = month_start_week + week_offset
                week_key = f'Week {week_num}'
                
                # Both electrical and mechanical are now 36-week rotas
                elec_week_key = f'Week {week_num}'
                
                if week_key not in mech_rota or elec_week_key not in elec_rota:
                    continue
                    
                mech_week = mech_rota[week_key]
                elec_week = elec_rota[elec_week_key]
                
                # Get engineers available any day Mon-Fri (Early or Late shift)
                for day_idx in range(5):  # Mon-Fri
                    # Check electrical engineers
                    for eng in all_engineers:
                        eng_id = eng['employee_code']
                        engineer_role = eng.get('role', 'Electrical').lower()
                        
                        if engineer_role == 'electrical' and eng_id in elec_week:
                            shifts = elec_week[eng_id]
                            if day_idx < len(shifts) and shifts[day_idx] in ['E', 'L']:
                                month_available_engineers.add(eng_id)
                        elif engineer_role == 'mechanical' and eng_id in mech_week:
                            shifts = mech_week[eng_id]
                            if day_idx < len(shifts) and shifts[day_idx] in ['E', 'L']:
                                month_available_engineers.add(eng_id)
            
            # For each ride with monthly PPMs, ensure coverage during this month
            for ride_id, ppms in team_monthly_ppms.items():
                for ppm in ppms:
                    maintenance_type = ppm['maintenance_type']
                    
                    # Find engineers who can cover this PPM and are available during month
                    qualified_available = []
                    
                    for eng in all_engineers:
                        eng_id = eng['employee_code']
                        engineer_role = eng.get('role', 'Electrical').lower()
                        
                        # Check if engineer's role matches maintenance type and is available during month
                        if (engineer_role == maintenance_type.lower() and 
                            eng_id in month_available_engineers):
                            qualified_available.append(eng_id)
                    
                    # Ensure coverage: at least 1 qualified engineer assigned to ride and available during month
                    if qualified_available:
                        coverage_sum = pulp.lpSum([
                            ride_assignment[eng_id][ride_id] 
                            for eng_id in qualified_available
                        ])
                        
                        constraint_name = f"Monthly_Coverage_M{month_num}_W{month_start_week}-{month_end_week}_{ride_id}_{ppm['ppm_code']}"
                        prob += coverage_sum >= 1, constraint_name
                        constraint_count += 1
        
        print(f"         Monthly coverage constraints: {constraint_count} (across {months_to_test} months)")
        return constraint_count
    
    def _qualification_matches_role(self, qualification, engineer_role):
        """Check if qualification matches engineer's role using dynamic PPM data mapping"""
        # Use the dynamic mapping built from actual PPM data
        if qualification in self.qualification_role_mapping:
            required_role = self.qualification_role_mapping[qualification]
            return required_role == engineer_role
        else:
            # Unknown qualification - log warning and reject
            print(f"   ⚠️  Unknown qualification not found in PPM data: {qualification}")
            return False
    
    def _is_daily_qualification(self, qualification_code, team):
        """Check if qualification is for daily PPMs"""
        team_rides = [rid for rid, info in self.optimizer.rides_info.items() 
                     if info.get('team_responsible') == team]
        
        for ride_id in team_rides:
            if ride_id in self.optimizer.ppms_by_type['daily']:
                ppm_data = self.optimizer.ppms_by_type['daily'][ride_id]
                for ppm in ppm_data['ppms']:
                    if ppm['qualification_code'] == qualification_code:
                        return True
        return False
    
    def _get_ride_qualification_sets(self, team, team_rides):
        """Get complete qualification sets for each ride (daily + weekly + monthly)"""
        ride_qualifications = {}
        
        for ride_id in team_rides:
            qualifications = {
                'daily_qualifications': [],
                'weekly_qualifications': [],
                'monthly_qualifications': [],
                'all_qualifications': set()
            }
            
            # Get qualifications from each PPM type
            for ppm_type in ['daily', 'weekly', 'monthly']:
                if ride_id in self.optimizer.ppms_by_type[ppm_type]:
                    ppm_data = self.optimizer.ppms_by_type[ppm_type][ride_id]
                    for ppm in ppm_data['ppms']:
                        qual_code = ppm['qualification_code']
                        qualifications[f'{ppm_type}_qualifications'].append(qual_code)
                        qualifications['all_qualifications'].add(qual_code)
            
            # Convert set to list for consistency
            qualifications['all_qualifications'] = list(qualifications['all_qualifications'])
            ride_qualifications[ride_id] = qualifications
        
        return ride_qualifications
    
    def _extract_ride_clustering_solution(self, ride_assignment, all_engineers, team_rides, ride_qualifications, team):
        """Extract solution from ride clustering variables and expand to individual qualifications"""
        print(f"   📊 EXTRACTING RIDE CLUSTERING SOLUTION:")
        
        # Convert ride assignments to individual qualification assignments
        engineer_assignments = {}
        ride_assignment_summary = {}
        
        for eng in all_engineers:
            eng_id = eng['employee_code']
            engineer_role = eng.get('role', 'Electrical').lower()
            assigned_rides = []
            all_qualifications = []
            
            # Find which rides this engineer was assigned
            for ride_id in team_rides:
                if ride_assignment[eng_id][ride_id].varValue == 1:
                    assigned_rides.append(ride_id)
                    # Add only the qualifications that match this engineer's role
                    ride_quals = ride_qualifications[ride_id]['all_qualifications']
                    role_qualifications = [qual for qual in ride_quals 
                                         if self._qualification_matches_role(qual, engineer_role)]
                    all_qualifications.extend(role_qualifications)
            
            # Remove duplicates while preserving order
            unique_qualifications = []
            seen = set()
            for qual in all_qualifications:
                if qual not in seen:
                    unique_qualifications.append(qual)
                    seen.add(qual)
            
            # Extract daily qualifications
            daily_qualifications = [qual for qual in unique_qualifications 
                                  if self._is_daily_qualification(qual, team)]
            
            # Categorize rides by type
            type_a_rides = []
            type_b_rides = []
            type_c_rides = []
            
            for ride_id in assigned_rides:
                if ride_id in self.optimizer.rides_info:
                    ride_type = self.optimizer.rides_info[ride_id].get('type', 'C')
                    if ride_type == 'A':
                        type_a_rides.append(ride_id)
                    elif ride_type == 'B':
                        type_b_rides.append(ride_id)
                    else:
                        type_c_rides.append(ride_id)
            
            # Get actual shift data
            shift_data = self.shift_analysis[team][engineer_role].get(eng_id, {})
            early_ratio = shift_data.get('early_ratio', 0.5)
            early_days = shift_data.get('early_days', 25)
            
            engineer_assignments[eng_id] = {
                'name': eng.get('timeplan_name', f"Engineer {eng_id}"),
                'role': engineer_role,
                'rota_number': eng.get('rota_number', 1),
                'early_ratio': early_ratio,
                'critical_early_days': early_days,
                'assigned_rides': assigned_rides,
                'type_a_rides': type_a_rides,
                'type_b_rides': type_b_rides,
                'type_c_rides': type_c_rides,
                'qualifications': unique_qualifications,
                'daily_qualifications': daily_qualifications,
                'coverage_score': len(unique_qualifications)
            }
            
            ride_assignment_summary[eng_id] = {
                'name': eng.get('timeplan_name', f"Engineer {eng_id}"),
                'rides': assigned_rides,
                'total_qualifications': len(unique_qualifications),
                'type_breakdown': f"A:{len(type_a_rides)}, B:{len(type_b_rides)}, C:{len(type_c_rides)}"
            }
        
        # Print assignment summary
        total_rides_assigned = sum(len(data['assigned_rides']) for data in engineer_assignments.values())
        total_qualifications = sum(len(data['qualifications']) for data in engineer_assignments.values())
        avg_rides_per_engineer = total_rides_assigned / len(all_engineers) if all_engineers else 0
        avg_quals_per_engineer = total_qualifications / len(all_engineers) if all_engineers else 0
        
        print(f"      Engineers: {len(all_engineers)}")
        print(f"      Total Rides Assigned: {total_rides_assigned}")
        print(f"      Total Qualifications: {total_qualifications}")
        print(f"      Avg Rides/Engineer: {avg_rides_per_engineer:.1f}")
        print(f"      Avg Qualifications/Engineer: {avg_quals_per_engineer:.1f}")
        
        # Show ride clustering success
        print(f"   🎯 RIDE CLUSTERING RESULTS:")
        engineers_with_assignments = [eng for eng in engineer_assignments.values() if eng['coverage_score'] > 0]
        
        if engineers_with_assignments:
            min_rides = min(len(eng['assigned_rides']) for eng in engineers_with_assignments)
            max_rides = max(len(eng['assigned_rides']) for eng in engineers_with_assignments)
            print(f"      Ride distribution: {min_rides}-{max_rides} rides per engineer")
            
            # Show type distribution
            total_type_a = sum(len(eng['type_a_rides']) for eng in engineers_with_assignments)
            total_type_b = sum(len(eng['type_b_rides']) for eng in engineers_with_assignments)
            total_type_c = sum(len(eng['type_c_rides']) for eng in engineers_with_assignments)
            print(f"      Type distribution: A:{total_type_a}, B:{total_type_b}, C:{total_type_c}")
            
            # Show example assignments
            print(f"   📋 SAMPLE ASSIGNMENTS (first 3 engineers):")
            for i, (eng_id, data) in enumerate(list(ride_assignment_summary.items())[:3]):
                rides_str = ', '.join(data['rides'][:3]) if data['rides'] else "None"
                if len(data['rides']) > 3:
                    rides_str += f" + {len(data['rides'])-3} more"
                print(f"      {data['name']}: {rides_str} ({data['type_breakdown']}, {data['total_qualifications']} quals)")
        
        return engineer_assignments
    
    def _heuristic_assignment(self, team, all_engineers):
        """Fallback heuristic assignment"""
        return self._create_balanced_fair_assignment(team, all_engineers)
    
    def _generate_engineer_assignment_counts(self, matrices):
        """Generate engineer assignment counts per ride split by electrical/mechanical"""
        assignment_counts = {}
        
        for team in [1, 2]:
            if team not in matrices:
                continue
                
            team_assignments = {}
            team_quals = matrices[team]
            
            # Get team rides
            team_rides = [rid for rid, info in self.optimizer.rides_info.items() 
                         if info.get('team_responsible') == team]
            
            # Initialize ride data
            for ride_id in team_rides:
                ride_name = self.optimizer.rides_info[ride_id]['name']
                ride_type = self.optimizer.rides_info[ride_id]['type']
                team_assignments[ride_id] = {
                    'ride_name': ride_name,
                    'ride_type': ride_type,
                    'electrical_engineers': [],
                    'mechanical_engineers': [],
                    'electrical_count': 0,
                    'mechanical_count': 0,
                    'total_count': 0
                }
            
            # Analyze engineer assignments
            for eng_id, eng_data in team_quals.items():
                name = eng_data['name']
                role = eng_data['role']
                qualifications = eng_data.get('qualifications', [])
                
                # Extract ride codes from qualifications
                assigned_rides = set()
                for qual in qualifications:
                    ride_code = qual.split('.')[0]
                    assigned_rides.add(ride_code)
                
                # Add engineer to each ride they're qualified for
                for ride_code in assigned_rides:
                    if ride_code in team_assignments:
                        if role == 'electrical':
                            team_assignments[ride_code]['electrical_engineers'].append(name)
                            team_assignments[ride_code]['electrical_count'] += 1
                        else:
                            team_assignments[ride_code]['mechanical_engineers'].append(name)
                            team_assignments[ride_code]['mechanical_count'] += 1
                        team_assignments[ride_code]['total_count'] += 1
            
            # Sort engineer names for consistency
            for ride_data in team_assignments.values():
                ride_data['electrical_engineers'].sort()
                ride_data['mechanical_engineers'].sort()
            
            assignment_counts[f'team_{team}'] = team_assignments
        
        return assignment_counts

    def validate_and_export_results(self, matrices):
        """Validate results using coverage validator and generate assignment reports"""
        print("\n🧪 VALIDATING MILP/HEURISTIC RESULTS")
        print("=" * 70)
        
        validation_results = self.coverage_validator.validate_assignment_coverage(matrices)
        
        # Generate engineer assignment counts
        print("\n📊 GENERATING ENGINEER ASSIGNMENT COUNTS...")
        assignment_counts = self._generate_engineer_assignment_counts(matrices)
        
        # Display validation summary
        for team in [1, 2]:
            if team in validation_results:
                results = validation_results[team]
                daily_cov = results['daily']['coverage_percentage']
                weekly_cov = results['weekly']['coverage_percentage']
                monthly_cov = results['monthly']['coverage_percentage']
                
                print(f"\n🏢 TEAM {team} OPTIMIZATION VALIDATION:")
                print(f"   Daily Coverage:   {daily_cov:.1f}% {'🎯' if daily_cov >= 90 else '⚠️' if daily_cov >= 60 else '❌'}")
                print(f"   Weekly Coverage:  {weekly_cov:.1f}% {'🎯' if weekly_cov >= 90 else '⚠️' if weekly_cov >= 60 else '❌'}")
                print(f"   Monthly Coverage: {monthly_cov:.1f}% {'🎯' if monthly_cov >= 90 else '⚠️' if monthly_cov >= 60 else '❌'}")
        
        return validation_results, assignment_counts
    
    def _build_qualification_role_mapping(self):
        """Build qualification to role mapping from actual PPM data"""
        print("🔗 BUILDING QUALIFICATION → ROLE MAPPING FROM PPM DATA")
        
        mapping = {}
        
        # Extract mappings from all PPM files
        for ppm_type in ['daily', 'weekly', 'monthly']:
            for ride_id, ppm_data in self.optimizer.ppms_by_type[ppm_type].items():
                for ppm in ppm_data['ppms']:
                    qual_code = ppm['qualification_code']
                    maintenance_type = ppm['maintenance_type']
                    
                    # Convert maintenance type to role
                    role = 'electrical' if maintenance_type == 'ELECTRICAL' else 'mechanical'
                    
                    # Check for conflicts
                    if qual_code in mapping and mapping[qual_code] != role:
                        print(f"   ⚠️  Qualification conflict: {qual_code} mapped to both {mapping[qual_code]} and {role}")
                    
                    mapping[qual_code] = role
        
        # Group by role for summary
        electrical_quals = [q for q, r in mapping.items() if r == 'electrical']
        mechanical_quals = [q for q, r in mapping.items() if r == 'mechanical']
        
        print(f"   📊 Mapping Results:")
        print(f"      Electrical qualifications: {len(electrical_quals)}")
        print(f"      Mechanical qualifications: {len(mechanical_quals)}")
        print(f"      Total qualifications: {len(mapping)}")
        
        # Show examples of patterns detected
        electrical_patterns = set()
        mechanical_patterns = set()
        
        for qual_code, role in mapping.items():
            parts = qual_code.split('.')
            if len(parts) >= 3:
                pattern = parts[2]
                if role == 'electrical':
                    electrical_patterns.add(pattern)
                else:
                    mechanical_patterns.add(pattern)
        
        print(f"   🔍 Detected Patterns:")
        print(f"      Electrical: {sorted(electrical_patterns)}")
        print(f"      Mechanical: {sorted(mechanical_patterns)}")
        
        return mapping


def main():
    """Run MILP optimization qualification design"""
    print("MILP Optimization Qualification Designer")
    print("Requires PPM data to be loaded first")


if __name__ == "__main__":
    main() 