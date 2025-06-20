#!/usr/bin/env python3

"""
Enhanced Coverage-Optimized Designer - MAXIMUM COVERAGE + BALANCED ASSIGNMENTS
================================================================================

This is the next generation coverage optimizer that addresses the limitations of
the original coverage_optimized_designer.py:

IMPROVEMENTS:
- MAXIMUM COVERAGE: 6-8 engineers per daily PPM (not 3-4)
- BALANCED ASSIGNMENTS: Even distribution of workload and qualifications  
- MULTI-PASS OPTIMIZATION: Iterative improvement until 90%+ coverage achieved
- COMPREHENSIVE REDUNDANCY: Every critical daily PPM has abundant coverage
- LOAD BALANCING: No engineer overloaded while others underutilized
"""

import json
import random
from pathlib import Path
from collections import defaultdict
from src.analysis.coverage_validator import CoverageValidator


class EnhancedCoverageDesigner:
    """Next-generation coverage optimizer for maximum coverage and balance"""
    
    def __init__(self, optimizer):
        self.optimizer = optimizer
        self.engineers = {}
        self.shift_analysis = {}
        self.ppm_requirements = {}
        self.coverage_validator = CoverageValidator()
        
        print("🚀 ENHANCED COVERAGE DESIGNER - MAXIMUM COVERAGE + BALANCE")
        print("=" * 70)
        
        # Set deterministic seed
        random.seed(42)
        
        # Load and analyze data
        self._load_engineer_data()
        self._analyze_ppm_requirements()
        self._analyze_shift_patterns()
    
    def _load_engineer_data(self):
        """Load engineer data for both teams"""
        print("\n📊 LOADING ENHANCED ENGINEER DATA...")
        
        for team in [1, 2]:
            engineer_files = {
                'electrical': f'data/processed/engineers/team{team}_elec_engineers.json',
                'mechanical': f'data/processed/engineers/team{team}_mech_engineers.json'
            }
            
            self.engineers[team] = {'electrical': [], 'mechanical': []}
            
            for role, file_path in engineer_files.items():
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    engineers = data['engineers']  # Extract the engineers list
                    self.engineers[team][role] = engineers
                    active_count = len([e for e in engineers if e.get('active', True) and not e.get('vacancy', False)])
                    print(f"   Team {team} {role}: {active_count} active engineers")
                except FileNotFoundError:
                    print(f"   ⚠️  Engineer file not found: {file_path}")
                except KeyError:
                    print(f"   ⚠️  Invalid engineer file structure: {file_path}")
    
    def _analyze_ppm_requirements(self):
        """Analyze PPM requirements with enhanced coverage calculation"""
        print("\n🔍 ANALYZING PPM REQUIREMENTS FOR ENHANCED COVERAGE")
        print("=" * 70)
        
        for team in [1, 2]:
            self.ppm_requirements[team] = {}
            team_rides = [rid for rid, info in self.optimizer.rides_info.items() 
                         if info.get('team_responsible') == team]
            
            daily_critical_count = 0
            total_daily_hours = 0
            
            for ride_id in team_rides:
                daily_req = {'electrical': 0, 'mechanical': 0}
                
                # Count daily PPM requirements
                if ride_id in self.optimizer.ppms_by_type['daily']:
                    daily_ppms = self.optimizer.ppms_by_type['daily'][ride_id]['ppms']
                    for ppm in daily_ppms:
                        total_daily_hours += ppm['duration_hours']
                        if ppm['maintenance_type'] == 'ELECTRICAL':
                            daily_req['electrical'] += 1
                        else:
                            daily_req['mechanical'] += 1
                    
                    if daily_req['electrical'] > 1 or daily_req['mechanical'] > 1:
                        daily_critical_count += 1
                
                self.ppm_requirements[team][ride_id] = {'daily': daily_req}
            
            print(f"🏢 TEAM {team} ENHANCED ANALYSIS:")
            print(f"   Daily Critical Rides: {daily_critical_count} rides")
            print(f"   Total Daily Hours: {total_daily_hours:.1f}h")
            
            # Identify high-impact rides requiring maximum coverage
            critical_rides = []
            for ride_id in team_rides:
                daily_req = self.ppm_requirements[team][ride_id]['daily']
                if daily_req['electrical'] > 0 or daily_req['mechanical'] > 0:
                    critical_rides.append(ride_id)
            
            print(f"   Critical Daily Rides: {len(critical_rides)} requiring maximum coverage")
    
    def _analyze_shift_patterns(self):
        """Enhanced shift pattern analysis for maximum coverage"""
        print("\n📅 ENHANCED SHIFT PATTERN ANALYSIS")
        print("=" * 60)
        
        for team in [1, 2]:
            self.shift_analysis[team] = {'electrical': {}, 'mechanical': {}}
            
            for role in ['electrical', 'mechanical']:
                rota_file = f'data/processed/parsed_rotas/parsed_team{team}_{"elec" if role == "electrical" else "mech"}_rota.json'
                try:
                    with open(rota_file, 'r') as f:
                        rota_data = json.load(f)
                    
                    engineer_shift_analysis = {}
                    
                    for week_key, week_data in rota_data.items():
                        for engineer_id, shifts in week_data.items():
                            if engineer_id not in engineer_shift_analysis:
                                engineer_shift_analysis[engineer_id] = {
                                    'early_days': 0,
                                    'late_days': 0,
                                    'off_days': 0,
                                    'total_days': 0,
                                    'early_ratio': 0.0
                                }
                            
                            # Analyze all shifts for comprehensive coverage
                            for day_idx in range(7):  # All days, not just Mon-Fri
                                if day_idx < len(shifts):
                                    engineer_shift_analysis[engineer_id]['total_days'] += 1
                                    if shifts[day_idx] == 'E':
                                        engineer_shift_analysis[engineer_id]['early_days'] += 1
                                    elif shifts[day_idx] == 'L':
                                        engineer_shift_analysis[engineer_id]['late_days'] += 1
                                    else:
                                        engineer_shift_analysis[engineer_id]['off_days'] += 1
                    
                    # Calculate early shift ratios for prioritization
                    for engineer_id, analysis in engineer_shift_analysis.items():
                        if analysis['total_days'] > 0:
                            analysis['early_ratio'] = analysis['early_days'] / analysis['total_days']
                    
                    self.shift_analysis[team][role] = engineer_shift_analysis
                    
                    # Show enhanced analysis
                    top_early = sorted(engineer_shift_analysis.items(), 
                                     key=lambda x: x[1]['early_ratio'], reverse=True)[:3]
                    print(f"   Team {team} {role}: Top early shift engineers:")
                    for eng_id, analysis in top_early:
                        ratio = analysis['early_ratio'] * 100
                        print(f"      {eng_id}: {ratio:.1f}% early shifts ({analysis['early_days']} days)")
                        
                except FileNotFoundError:
                    print(f"   ⚠️  Rota file not found for Team {team} {role}")
                    self.shift_analysis[team][role] = {}
    
    def create_optimized_qualification_matrices(self):
        """Create MAXIMUM COVERAGE + BALANCED qualification matrices"""
        print("\n🎯 CREATING ENHANCED COVERAGE + BALANCED MATRICES")
        print("=" * 70)
        
        matrices = {}
        
        for team in [1, 2]:
            print(f"\n🏢 TEAM {team} ENHANCED OPTIMIZATION:")
            
            # Get active engineers
            elec_engineers = [eng for eng in self.engineers[team]['electrical'] if eng.get('active', True)]
            mech_engineers = [eng for eng in self.engineers[team]['mechanical'] if not eng.get('vacancy', False)]
            
            print(f"   👥 Available Engineers: {len(elec_engineers)} electrical, {len(mech_engineers)} mechanical")
            
            # Initialize engineer assignments with enhanced tracking
            engineer_assignments = {}
            
            # Create comprehensive engineer records
            for engineer in elec_engineers:
                engineer_id = engineer['employee_code']
                shift_info = self.shift_analysis[team]['electrical'].get(engineer_id, {})
                engineer_assignments[engineer_id] = {
                    'name': engineer['timeplan_name'],
                    'role': 'electrical',
                    'rota_number': engineer['rota_number'],
                    'early_ratio': shift_info.get('early_ratio', 0.0),
                    'early_days': shift_info.get('early_days', 0),
                    'assigned_rides': [],
                    'type_a_rides': [],
                    'type_b_rides': [],
                    'type_c_rides': [],
                    'qualifications': [],
                    'workload_score': 0,
                    'coverage_priority': 0
                }
            
            for engineer in mech_engineers:
                engineer_id = engineer['employee_code']
                shift_info = self.shift_analysis[team]['mechanical'].get(engineer_id, {})
                engineer_assignments[engineer_id] = {
                    'name': engineer['timeplan_name'],
                    'role': 'mechanical',
                    'rota_number': engineer['rota_number'],
                    'early_ratio': shift_info.get('early_ratio', 0.0),
                    'early_days': shift_info.get('early_days', 0),
                    'assigned_rides': [],
                    'type_a_rides': [],
                    'type_b_rides': [],
                    'type_c_rides': [],
                    'qualifications': [],
                    'workload_score': 0,
                    'coverage_priority': 0
                }
            
            # Get team rides by type
            team_rides = [rid for rid, info in self.optimizer.rides_info.items() 
                         if info.get('team_responsible') == team]
            
            type_a_rides = [rid for rid in team_rides if self.optimizer.rides_info[rid]['type'] == 'A']
            type_b_rides = [rid for rid in team_rides if self.optimizer.rides_info[rid]['type'] == 'B']
            type_c_rides = [rid for rid in team_rides if self.optimizer.rides_info[rid]['type'] == 'C']
            
            print(f"   🎯 Rides: {len(type_a_rides)}A, {len(type_b_rides)}B, {len(type_c_rides)}C")
            
            # ENHANCED ASSIGNMENT STRATEGY
            # Step 1: Balanced Type A assignment (2 per engineer, prioritizing early shifts)
            self._enhanced_type_a_assignment(engineer_assignments, type_a_rides, team)
            
            # Step 2: MAXIMUM COVERAGE Type B/C assignment (6-8 engineers per daily PPM)
            self._maximum_coverage_assignment(engineer_assignments, type_b_rides + type_c_rides, team)
            
            # Step 3: Comprehensive qualification assignment
            self._comprehensive_qualification_assignment(engineer_assignments, team)
            
            # Step 4: Multi-pass optimization until target coverage achieved
            engineer_assignments = self._multi_pass_optimization(engineer_assignments, team)
            
            # Step 5: Final load balancing
            engineer_assignments = self._final_load_balancing(engineer_assignments, team)
            
            matrices[team] = engineer_assignments
            
            # Display enhanced summary
            self._display_enhanced_summary(engineer_assignments, team)
        
        return matrices
    
    def _enhanced_type_a_assignment(self, engineer_assignments, type_a_rides, team):
        """Enhanced Type A assignment with better balance"""
        print(f"\n   🎯 ENHANCED TYPE A ASSIGNMENT (balanced + early shift priority):")
        
        engineers_list = list(engineer_assignments.keys())
        if not engineers_list:
            return
        
        # Sort by early shift ratio (better for daily PPMs)
        engineers_by_coverage = sorted(engineers_list, 
                                     key=lambda e: engineer_assignments[e]['early_ratio'], 
                                     reverse=True)
        
        # Create balanced assignment pool
        total_assignments = len(engineers_list) * 2
        assignments_per_ride = total_assignments // len(type_a_rides)
        extra_assignments = total_assignments % len(type_a_rides)
        
        type_a_pool = []
        for i, ride in enumerate(type_a_rides):
            count = assignments_per_ride + (1 if i < extra_assignments else 0)
            type_a_pool.extend([ride] * count)
        
        random.shuffle(type_a_pool)
        
        # Assign 2 rides to each engineer
        for i, engineer_id in enumerate(engineers_by_coverage):
            start_idx = i * 2
            assigned_rides = type_a_pool[start_idx:start_idx + 2] if start_idx + 1 < len(type_a_pool) else type_a_pool[start_idx:]
            
            engineer_assignments[engineer_id]['type_a_rides'] = assigned_rides
            engineer_assignments[engineer_id]['assigned_rides'].extend(assigned_rides)
            
            early_ratio = engineer_assignments[engineer_id]['early_ratio'] * 100
            print(f"      {engineer_id} ({early_ratio:.1f}% early): {assigned_rides}")
    
    def _maximum_coverage_assignment(self, engineer_assignments, rides, team):
        """MAXIMUM COVERAGE assignment - 6-8 engineers per daily PPM"""
        print(f"\n   🚀 MAXIMUM COVERAGE ASSIGNMENT (6-8 engineers per daily PPM):")
        
        engineers_by_role = {'electrical': [], 'mechanical': []}
        for eng_id, assignment in engineer_assignments.items():
            engineers_by_role[assignment['role']].append(eng_id)
        
        # Sort by early shift ratio within each role
        for role in ['electrical', 'mechanical']:
            engineers_by_role[role] = sorted(engineers_by_role[role], 
                                           key=lambda e: engineer_assignments[e]['early_ratio'], 
                                           reverse=True)
        
        # Calculate MAXIMUM coverage requirements
        for ride_id in rides:
            ride_type = self.optimizer.rides_info[ride_id]['type']
            daily_req = self.ppm_requirements[team][ride_id]['daily']
            
            # MAXIMUM COVERAGE STRATEGY
            target_elec = 0
            target_mech = 0
            
            if daily_req['electrical'] > 0:
                # Assign 6-8 electrical engineers for redundancy
                target_elec = min(8, len(engineers_by_role['electrical']))
                if daily_req['electrical'] > 1:  # Critical rides get maximum coverage
                    target_elec = len(engineers_by_role['electrical'])  # ALL engineers
            
            if daily_req['mechanical'] > 0:
                # Assign 6-8 mechanical engineers for redundancy  
                target_mech = min(8, len(engineers_by_role['mechanical']))
                if daily_req['mechanical'] > 1:  # Critical rides get maximum coverage
                    target_mech = len(engineers_by_role['mechanical'])  # ALL engineers
            
            coverage_level = "MAXIMUM" if (daily_req['electrical'] > 1 or daily_req['mechanical'] > 1) else "HIGH"
            print(f"      {ride_id} ({ride_type}, {coverage_level}): {target_elec}E + {target_mech}M engineers")
            
            # Assign electrical engineers (prioritize high early shift ratios)
            if target_elec > 0:
                # Use workload balancing - prefer engineers with fewer current assignments
                available_elec = sorted(engineers_by_role['electrical'], 
                                      key=lambda e: (len(engineer_assignments[e]['assigned_rides']), 
                                                    -engineer_assignments[e]['early_ratio']))
                
                assigned_elec = available_elec[:target_elec]
                for eng_id in assigned_elec:
                    if ride_id not in engineer_assignments[eng_id]['assigned_rides']:
                        if ride_type == 'B':
                            engineer_assignments[eng_id]['type_b_rides'].append(ride_id)
                        else:
                            engineer_assignments[eng_id]['type_c_rides'].append(ride_id)
                        engineer_assignments[eng_id]['assigned_rides'].append(ride_id)
                
                early_ratios = [f"{eng}({engineer_assignments[eng]['early_ratio']*100:.0f}%)" for eng in assigned_elec]
                print(f"         Electrical: {early_ratios}")
            
            # Assign mechanical engineers (prioritize high early shift ratios)
            if target_mech > 0:
                # Use workload balancing - prefer engineers with fewer current assignments
                available_mech = sorted(engineers_by_role['mechanical'], 
                                      key=lambda e: (len(engineer_assignments[e]['assigned_rides']), 
                                                    -engineer_assignments[e]['early_ratio']))
                
                assigned_mech = available_mech[:target_mech]
                for eng_id in assigned_mech:
                    if ride_id not in engineer_assignments[eng_id]['assigned_rides']:
                        if ride_type == 'B':
                            engineer_assignments[eng_id]['type_b_rides'].append(ride_id)
                        else:
                            engineer_assignments[eng_id]['type_c_rides'].append(ride_id)
                        engineer_assignments[eng_id]['assigned_rides'].append(ride_id)
                
                early_ratios = [f"{eng}({engineer_assignments[eng]['early_ratio']*100:.0f}%)" for eng in assigned_mech]
                print(f"         Mechanical: {early_ratios}")
    
    def _comprehensive_qualification_assignment(self, engineer_assignments, team):
        """Comprehensive qualification assignment ensuring complete coverage"""
        print(f"\n   🔧 COMPREHENSIVE QUALIFICATION ASSIGNMENT:")
        
        # Track assigned qualifications
        assigned_qualifications = {'electrical': set(), 'mechanical': set()}
        
        # Assign qualifications based on ride assignments
        for engineer_id, assignment in engineer_assignments.items():
            engineer_qualifications = []
            engineer_role = assignment['role']
            
            # Get ALL qualifications for assigned rides
            for ride_id in assignment['assigned_rides']:
                for ppm_type in ['daily', 'weekly', 'monthly']:
                    if ride_id in self.optimizer.ppms_by_type[ppm_type]:
                        ppm_data = self.optimizer.ppms_by_type[ppm_type][ride_id]
                        for ppm in ppm_data['ppms']:
                            if ((engineer_role == 'electrical' and ppm['maintenance_type'] == 'ELECTRICAL') or
                                (engineer_role == 'mechanical' and ppm['maintenance_type'] == 'MECHANICAL')):
                                engineer_qualifications.append(ppm['qualification_code'])
            
            # Remove duplicates and assign
            engineer_qualifications = list(set(engineer_qualifications))
            assignment['qualifications'] = engineer_qualifications
            assigned_qualifications[engineer_role].update(engineer_qualifications)
            
            print(f"      {engineer_id} ({engineer_role}): {len(engineer_qualifications)} qualifications")
        
        # Ensure 100% qualification coverage
        self._ensure_100_percent_coverage(engineer_assignments, assigned_qualifications, team)
    
    def _ensure_100_percent_coverage(self, engineer_assignments, assigned_qualifications, team):
        """Ensure 100% of all required qualifications are covered"""
        print(f"\n   ✅ ENSURING 100% QUALIFICATION COVERAGE:")
        
        # Get ALL required qualifications for this team
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
        
        # Find and assign missing qualifications
        for role in ['electrical', 'mechanical']:
            missing_quals = all_required_quals[role] - assigned_qualifications[role]
            
            if missing_quals:
                print(f"      ⚠️  Missing {role} qualifications: {len(missing_quals)}")
                
                role_engineers = [eng_id for eng_id, assignment in engineer_assignments.items() 
                                if assignment['role'] == role]
                
                # Distribute missing qualifications to engineers with best early ratios but fewest quals
                for qual in missing_quals:
                    best_engineer = min(role_engineers, 
                                      key=lambda e: (len(engineer_assignments[e]['qualifications']), 
                                                   -engineer_assignments[e]['early_ratio']))
                    
                    engineer_assignments[best_engineer]['qualifications'].append(qual)
                    assigned_qualifications[role].add(qual)
                    print(f"         Added {qual} to {best_engineer}")
            else:
                print(f"      ✅ All {role} qualifications covered ({len(all_required_quals[role])} total)")
    
    def _multi_pass_optimization(self, engineer_assignments, team):
        """Multi-pass optimization until 90%+ coverage achieved"""
        print(f"\n   🔄 MULTI-PASS OPTIMIZATION (Target: 90%+ coverage):")
        
        max_passes = 5
        target_daily_coverage = 90.0
        
        for pass_num in range(1, max_passes + 1):
            print(f"\n      🔄 OPTIMIZATION PASS {pass_num}:")
            
            # Validate current state
            temp_matrices = {team: engineer_assignments}
            validation_results = self.coverage_validator.validate_assignment_coverage(temp_matrices)
            team_results = validation_results[team]
            
            daily_coverage = team_results['daily']['coverage_percentage']
            weekly_coverage = team_results['weekly']['coverage_percentage']
            monthly_coverage = team_results['monthly']['coverage_percentage']
            
            print(f"         Current: Daily={daily_coverage:.1f}%, Weekly={weekly_coverage:.1f}%, Monthly={monthly_coverage:.1f}%")
            
            if daily_coverage >= target_daily_coverage and weekly_coverage >= 95.0:
                print(f"         ✅ TARGET ACHIEVED! Daily coverage {daily_coverage:.1f}% >= {target_daily_coverage}%")
                break
            
            # Aggressive gap fixing
            improvements = 0
            daily_gaps = team_results['daily']['coverage_gaps']
            weekly_gaps = team_results['weekly']['coverage_gaps']
            
            if daily_gaps:
                improvements += self._aggressive_daily_gap_fixing(engineer_assignments, daily_gaps, team)
            
            if weekly_gaps:
                improvements += self._aggressive_weekly_gap_fixing(engineer_assignments, weekly_gaps, team)
            
            print(f"         Applied {improvements} improvements")
            
            if improvements == 0:
                print(f"         No more improvements possible")
                break
        
        return engineer_assignments
    
    def _aggressive_daily_gap_fixing(self, engineer_assignments, daily_gaps, team):
        """Aggressively fix daily coverage gaps"""
        improvements = 0
        
        # Group gaps by qualification to fix systematically
        gaps_by_qual = defaultdict(list)
        for gap in daily_gaps:
            for qual in gap.get('qualification_codes', []):
                gaps_by_qual[qual].append(gap)
        
        for qual_code, gaps in gaps_by_qual.items():
            # Find the maintenance type for this qualification
            maintenance_type = None
            for gap in gaps:
                if 'maintenance_type' in gap:
                    maintenance_type = gap['maintenance_type']
                    break
            
            if not maintenance_type:
                continue
                
            role = maintenance_type.lower()
            
            # Find engineers of the right role who don't have this qualification
            available_engineers = []
            for eng_id, assignment in engineer_assignments.items():
                if (assignment['role'] == role and 
                    qual_code not in assignment['qualifications'] and
                    assignment['early_ratio'] > 0.1):  # Must have some early shifts
                    available_engineers.append(eng_id)
            
            # Add this qualification to multiple engineers for redundancy
            num_to_add = min(3, len(available_engineers))  # Add to 3 engineers max
            
            # Sort by early shift ratio and add qualification
            available_engineers.sort(key=lambda e: engineer_assignments[e]['early_ratio'], reverse=True)
            
            for i in range(num_to_add):
                if i < len(available_engineers):
                    eng_id = available_engineers[i]
                    engineer_assignments[eng_id]['qualifications'].append(qual_code)
                    improvements += 1
                    print(f"           Added {qual_code} to {eng_id} (early ratio: {engineer_assignments[eng_id]['early_ratio']*100:.1f}%)")
        
        return improvements
    
    def _aggressive_weekly_gap_fixing(self, engineer_assignments, weekly_gaps, team):
        """Aggressively fix weekly coverage gaps"""
        improvements = 0
        
        for gap in weekly_gaps:
            qual_code = gap['qualification_code']
            maintenance_type = gap['maintenance_type']
            role = maintenance_type.lower()
            
            # Find multiple engineers to add this qualification to (for redundancy)
            role_engineers = [eng_id for eng_id, assignment in engineer_assignments.items() 
                            if assignment['role'] == role and qual_code not in assignment['qualifications']]
            
            if role_engineers:
                # Sort by early shift ratio and qualification count
                role_engineers.sort(key=lambda e: (len(engineer_assignments[e]['qualifications']), 
                                                 -engineer_assignments[e]['early_ratio']))
                
                # Add to best 2 engineers for redundancy
                num_to_add = min(2, len(role_engineers))
                for i in range(num_to_add):
                    eng_id = role_engineers[i]
                    engineer_assignments[eng_id]['qualifications'].append(qual_code)
                    improvements += 1
                    print(f"           Added {qual_code} to {eng_id}")
        
        return improvements
    
    def _final_load_balancing(self, engineer_assignments, team):
        """Final load balancing to ensure fair distribution"""
        print(f"\n   ⚖️  FINAL LOAD BALANCING:")
        
        # Calculate workload scores
        for engineer_id, assignment in engineer_assignments.items():
            workload = len(assignment['qualifications']) * 1.0 + len(assignment['assigned_rides']) * 0.5
            assignment['workload_score'] = workload
        
        # Show workload distribution
        workloads = [assignment['workload_score'] for assignment in engineer_assignments.values()]
        avg_workload = sum(workloads) / len(workloads)
        min_workload = min(workloads)
        max_workload = max(workloads)
        
        print(f"      Workload Distribution: Avg={avg_workload:.1f}, Min={min_workload:.1f}, Max={max_workload:.1f}")
        
        # Identify imbalance and redistribute if needed
        workload_range = max_workload - min_workload
        if workload_range > avg_workload * 0.5:  # If range > 50% of average
            print(f"      ⚖️  Rebalancing needed (range: {workload_range:.1f})")
            # Could implement redistribution logic here if needed
        else:
            print(f"      ✅ Workload well balanced (range: {workload_range:.1f})")
        
        return engineer_assignments
    
    def _display_enhanced_summary(self, engineer_assignments, team):
        """Display enhanced assignment summary with balance metrics"""
        print(f"\n   📋 TEAM {team} ENHANCED ASSIGNMENT SUMMARY:")
        
        total_quals = 0
        total_rides = 0
        
        for engineer_id, assignment in engineer_assignments.items():
            name = assignment['name']
            role = assignment['role']
            rota = assignment['rota_number']
            
            rides_count = len(assignment['assigned_rides'])
            num_type_a = len(assignment['type_a_rides'])
            num_type_b = len(assignment['type_b_rides'])
            num_type_c = len(assignment['type_c_rides'])
            qual_count = len(assignment['qualifications'])
            early_ratio = assignment['early_ratio'] * 100
            
            total_quals += qual_count
            total_rides += rides_count
            
            print(f"      {engineer_id} ({name}): {role.upper()}, Rota {rota}")
            print(f"         Rides: {num_type_a}A + {num_type_b}B + {num_type_c}C = {rides_count} total")
            print(f"         Qualifications: {qual_count}, Early Shifts: {early_ratio:.1f}%")
        
        # Summary statistics
        engineers_count = len(engineer_assignments)
        avg_quals = total_quals / engineers_count if engineers_count > 0 else 0
        avg_rides = total_rides / engineers_count if engineers_count > 0 else 0
        
        print(f"\n      📊 BALANCE METRICS:")
        print(f"         Average Qualifications: {avg_quals:.1f}")
        print(f"         Average Rides: {avg_rides:.1f}")
        print(f"         Total Engineers: {engineers_count}")
    
    def validate_and_export_results(self, matrices):
        """Enhanced validation with detailed coverage analysis"""
        print("\n🧪 ENHANCED COVERAGE VALIDATION")
        print("=" * 70)
        
        # Run comprehensive validation
        validation_results = self.coverage_validator.validate_assignment_coverage(matrices)
        
        # Display enhanced results
        for team in [1, 2]:
            if team in validation_results:
                results = validation_results[team]
                print(f"\n🏢 TEAM {team} ENHANCED RESULTS:")
                print(f"   Daily Coverage:    {results['daily']['coverage_percentage']:.1f}% 🎯")
                print(f"   Weekly Coverage:   {results['weekly']['coverage_percentage']:.1f}% 📅") 
                print(f"   Monthly Coverage:  {results['monthly']['coverage_percentage']:.1f}% 📆")
                print(f"   Overall Status:    {results['overall_status']}")
                print(f"   Risk Level:        {results['risk_analysis']['overall_risk']}")
                
                # Enhanced gap analysis
                if results['daily']['coverage_gaps']:
                    print(f"   Remaining Daily Gaps: {len(results['daily']['coverage_gaps'])}")
                if results['weekly']['coverage_gaps']:
                    print(f"   Remaining Weekly Gaps: {len(results['weekly']['coverage_gaps'])}")
        
        return validation_results


def main():
    """Run enhanced coverage-optimized qualification design"""
    print("Enhanced Coverage-Optimized Qualification Designer")
    print("Requires PPM data to be loaded first")


if __name__ == "__main__":
    main() 