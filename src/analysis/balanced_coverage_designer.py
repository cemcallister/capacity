#!/usr/bin/env python3

"""
Balanced Coverage Qualification Designer
========================================

This module creates qualification matrices that balance workload evenly across
all engineers while ensuring adequate coverage for daily, weekly, and monthly PPMs
during the appropriate time windows.

Key Features:
- Even distribution of qualifications across all engineers
- Maximum and minimum qualification limits per engineer
- Proper coverage during shift windows
- Role-based qualification filtering
- Balanced workload assignment
"""

import json
import random
import math
from pathlib import Path
from collections import defaultdict, Counter

from .coverage_validator import CoverageValidator


class BalancedCoverageDesigner:
    """Balanced qualification assignment with even workload distribution"""
    
    def __init__(self, optimizer_results):
        """Initialize with PPM optimization results"""
        self.optimizer = optimizer_results
        self.engineers = self._load_engineer_data()
        self.ppm_requirements = self._analyze_ppm_requirements()
        self.shift_analysis = self._analyze_shift_patterns()
        self.coverage_validator = CoverageValidator()
        
        print("⚖️  BALANCED COVERAGE DESIGNER INITIALIZED")
        print("   Focus: Even qualification distribution + adequate coverage")
    
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
        """Analyze PPM requirements for each team and ride"""
        requirements = {1: {}, 2: {}}
        
        for team in [1, 2]:
            team_rides = [rid for rid, info in self.optimizer.rides_info.items() 
                         if info.get('team_responsible') == team]
            
            for ride_id in team_rides:
                requirements[team][ride_id] = {
                    'daily': {'electrical': 0, 'mechanical': 0},
                    'weekly': {'electrical': 0, 'mechanical': 0},
                    'monthly': {'electrical': 0, 'mechanical': 0},
                    'qualifications': {'electrical': set(), 'mechanical': set()}
                }
                
                # Analyze each PPM type
                for ppm_type in ['daily', 'weekly', 'monthly']:
                    if ride_id in self.optimizer.ppms_by_type[ppm_type]:
                        ppm_data = self.optimizer.ppms_by_type[ppm_type][ride_id]
                        
                        for ppm in ppm_data['ppms']:
                            role = 'electrical' if ppm['maintenance_type'] == 'ELECTRICAL' else 'mechanical'
                            
                            # Count engineer requirements
                            engineer_req = ppm.get('engineers_required', 1)
                            requirements[team][ride_id][ppm_type][role] += engineer_req
                            
                            # Collect qualifications
                            requirements[team][ride_id]['qualifications'][role].add(ppm['qualification_code'])
        
        return requirements
    
    def _analyze_shift_patterns(self):
        """Analyze shift patterns to understand early shift availability"""
        print("📅 ANALYZING SHIFT PATTERNS FOR BALANCED OPTIMIZATION")
        
        shift_analysis = {}
        
        for team in [1, 2]:
            shift_analysis[team] = {'electrical': {}, 'mechanical': {}}
            
            for role in ['electrical', 'mechanical']:
                rota_file = f'data/processed/parsed_rotas/parsed_team{team}_{"elec" if role == "electrical" else "mech"}_rota.json'
                try:
                    with open(rota_file, 'r') as f:
                        rota_data = json.load(f)
                    
                    engineer_early_days = {}
                    engineer_early_ratio = {}
                    
                    for week_key, week_data in rota_data.items():
                        for engineer_id, shifts in week_data.items():
                            if engineer_id not in engineer_early_days:
                                engineer_early_days[engineer_id] = 0
                            
                            # Count early shifts Monday-Friday (critical for daily PPMs)
                            early_count = 0
                            total_weekdays = 0
                            for day_idx in range(min(5, len(shifts))):  # Mon-Fri only
                                total_weekdays += 1
                                if shifts[day_idx] == 'E':
                                    early_count += 1
                                    engineer_early_days[engineer_id] += 1
                            
                            if total_weekdays > 0:
                                engineer_early_ratio[engineer_id] = early_count / total_weekdays
                    
                    shift_analysis[team][role] = {
                        'early_days': engineer_early_days,
                        'early_ratio': engineer_early_ratio
                    }
                    
                    print(f"   Team {team} {role}: Analyzed {len(engineer_early_days)} engineers")
                    
                except FileNotFoundError:
                    print(f"   ⚠️  Rota file not found for Team {team} {role}")
                    shift_analysis[team][role] = {'early_days': {}, 'early_ratio': {}}
        
        return shift_analysis
    
    def create_optimized_qualification_matrices(self):
        """Create balanced qualification matrices"""
        print("\n⚖️  CREATING BALANCED QUALIFICATION MATRICES")
        print("=" * 70)
        
        matrices = {}
        
        for team in [1, 2]:
            print(f"\n🏢 TEAM {team} BALANCED OPTIMIZATION:")
            
            # Get active engineers
            elec_engineers = [eng for eng in self.engineers[team]['electrical'] if eng.get('active', True)]
            mech_engineers = [eng for eng in self.engineers[team]['mechanical'] if not eng.get('vacancy', False)]
            
            print(f"   👥 Available Engineers: {len(elec_engineers)} electrical, {len(mech_engineers)} mechanical")
            
            # Calculate total qualification requirements
            total_quals_needed = self._calculate_total_qualifications_needed(team)
            
            # Initialize balanced engineer assignments
            engineer_assignments = self._initialize_balanced_assignments(team, elec_engineers, mech_engineers, total_quals_needed)
            
            # STEP 1: Assign Type A rides evenly (each engineer gets exactly 2)
            self._assign_type_a_rides_balanced(engineer_assignments, team)
            
            # STEP 2: Distribute qualifications evenly across engineers
            self._distribute_qualifications_evenly(engineer_assignments, team)
            
            # STEP 3: Ensure adequate coverage during shift windows
            self._ensure_shift_window_coverage(engineer_assignments, team)
            
            # STEP 4: Balance and validate
            engineer_assignments = self._balance_and_validate(engineer_assignments, team)
            
            matrices[team] = engineer_assignments
            
            # Display balanced summary
            self._display_balanced_summary(engineer_assignments, team)
        
        return matrices
    
    def _calculate_total_qualifications_needed(self, team):
        """Calculate total qualifications needed for the team"""
        all_quals = {'electrical': set(), 'mechanical': set()}
        
        team_rides = [rid for rid, info in self.optimizer.rides_info.items() 
                     if info.get('team_responsible') == team]
        
        for ride_id in team_rides:
            for role in ['electrical', 'mechanical']:
                all_quals[role].update(self.ppm_requirements[team][ride_id]['qualifications'][role])
        
        print(f"   📊 Total Qualifications Needed:")
        print(f"      Electrical: {len(all_quals['electrical'])} unique qualifications")
        print(f"      Mechanical: {len(all_quals['mechanical'])} unique qualifications")
        
        return all_quals
    
    def _initialize_balanced_assignments(self, team, elec_engineers, mech_engineers, total_quals_needed):
        """Initialize balanced engineer assignments with target qualification counts"""
        engineer_assignments = {}
        
        # Calculate target qualifications per engineer
        elec_count = len(elec_engineers)
        mech_count = len(mech_engineers)
        
        # Set balanced targets with min/max limits
        elec_quals_total = len(total_quals_needed['electrical'])
        mech_quals_total = len(total_quals_needed['mechanical'])
        
        # More conservative targets for balanced distribution
        elec_target = math.ceil(elec_quals_total * 1.3 / elec_count) if elec_count > 0 else 0  # 1.3x for redundancy
        mech_target = math.ceil(mech_quals_total * 1.3 / mech_count) if mech_count > 0 else 0
        
        # Set reasonable limits to prevent super engineers
        elec_min = max(4, elec_target - 3)
        elec_max = min(15, elec_target + 5)  # Tighter max limit
        mech_min = max(6, mech_target - 4)  
        mech_max = min(20, mech_target + 6)  # Tighter max limit
        
        print(f"   🎯 Balanced Targets:")
        print(f"      Electrical: {elec_min}-{elec_max} qualifications per engineer (target: {elec_target})")
        print(f"      Mechanical: {mech_min}-{mech_max} qualifications per engineer (target: {mech_target})")
        
        # Initialize electrical engineers
        for engineer in elec_engineers:
            engineer_id = engineer['employee_code']
            engineer_assignments[engineer_id] = {
                'name': engineer['timeplan_name'],
                'role': 'electrical',
                'rota_number': engineer['rota_number'],
                'early_ratio': self.shift_analysis[team]['electrical']['early_ratio'].get(engineer_id, 0),
                'critical_early_days': self.shift_analysis[team]['electrical']['early_days'].get(engineer_id, 0),
                'target_qualifications': elec_target,
                'min_qualifications': elec_min,
                'max_qualifications': elec_max,
                'assigned_rides': [],
                'type_a_rides': [],
                'type_b_rides': [],
                'type_c_rides': [],
                'qualifications': [],
                'daily_qualifications': [],
                'coverage_score': 0
            }
        
        # Initialize mechanical engineers
        for engineer in mech_engineers:
            engineer_id = engineer['employee_code']
            engineer_assignments[engineer_id] = {
                'name': engineer['timeplan_name'],
                'role': 'mechanical',
                'rota_number': engineer['rota_number'],
                'early_ratio': self.shift_analysis[team]['mechanical']['early_ratio'].get(engineer_id, 0),
                'critical_early_days': self.shift_analysis[team]['mechanical']['early_days'].get(engineer_id, 0),
                'target_qualifications': mech_target,
                'min_qualifications': mech_min,
                'max_qualifications': mech_max,
                'assigned_rides': [],
                'type_a_rides': [],
                'type_b_rides': [],
                'type_c_rides': [],
                'qualifications': [],
                'daily_qualifications': [],
                'coverage_score': 0
            }
        
        return engineer_assignments
    
    def _assign_type_a_rides_balanced(self, engineer_assignments, team):
        """Assign Type A rides evenly across all engineers"""
        print(f"\n   🎯 BALANCED TYPE A ASSIGNMENT:")
        
        # Get Type A rides for this team
        team_rides = [rid for rid, info in self.optimizer.rides_info.items() 
                     if info.get('team_responsible') == team]
        type_a_rides = [rid for rid in team_rides if self.optimizer.rides_info[rid]['type'] == 'A']
        
        engineers_list = list(engineer_assignments.keys())
        total_engineers = len(engineers_list)
        
        if total_engineers == 0 or len(type_a_rides) == 0:
            print("      ⚠️  No engineers or Type A rides available!")
            return
        
        print(f"      📊 Distributing {len(type_a_rides)} Type A rides across {total_engineers} engineers")
        
        # Create balanced assignment pool (each engineer gets exactly 2 rides)
        assignments_needed = total_engineers * 2
        assignments_per_ride = assignments_needed // len(type_a_rides)
        extra_assignments = assignments_needed % len(type_a_rides)
        
        type_a_pool = []
        for i, ride in enumerate(type_a_rides):
            count = assignments_per_ride + (1 if i < extra_assignments else 0)
            type_a_pool.extend([ride] * count)
        
        # Shuffle for randomness while maintaining balance
        random.shuffle(type_a_pool)
        
        # Assign exactly 2 rides to each engineer
        for i, engineer_id in enumerate(engineers_list):
            start_idx = i * 2
            assigned_rides = type_a_pool[start_idx:start_idx + 2] if start_idx + 1 < len(type_a_pool) else type_a_pool[start_idx:]
            
            engineer_assignments[engineer_id]['type_a_rides'] = assigned_rides
            engineer_assignments[engineer_id]['assigned_rides'].extend(assigned_rides)
            
            print(f"         {engineer_id}: {assigned_rides}")
    
    def _distribute_qualifications_evenly(self, engineer_assignments, team):
        """Distribute qualifications evenly across engineers while maintaining role filtering"""
        print(f"\n   ⚖️  DISTRIBUTING QUALIFICATIONS EVENLY:")
        
        # Get all qualifications needed for this team by role
        team_rides = [rid for rid, info in self.optimizer.rides_info.items() 
                     if info.get('team_responsible') == team]
        
        all_qualifications = {'electrical': [], 'mechanical': []}
        
        for ride_id in team_rides:
            for ppm_type in ['daily', 'weekly', 'monthly']:
                if ride_id in self.optimizer.ppms_by_type[ppm_type]:
                    ppm_data = self.optimizer.ppms_by_type[ppm_type][ride_id]
                    for ppm in ppm_data['ppms']:
                        role = 'electrical' if ppm['maintenance_type'] == 'ELECTRICAL' else 'mechanical'
                        all_qualifications[role].append(ppm['qualification_code'])
        
        # Create redundancy for critical qualifications but maintain balance
        for role in ['electrical', 'mechanical']:
            unique_quals = list(set(all_qualifications[role]))
            balanced_quals = []
            
            # Each qualification gets appropriate redundancy
            for qual in unique_quals:
                # Daily qualifications get 2 copies, others get 1
                if self._is_daily_qualification(qual, team):
                    balanced_quals.extend([qual] * 2)  # Reduced from 3 for better balance
                else:
                    balanced_quals.append(qual)
            
            all_qualifications[role] = balanced_quals
        
        # Distribute to engineers by role
        for role in ['electrical', 'mechanical']:
            role_engineers = [eng_id for eng_id, assignment in engineer_assignments.items() 
                            if assignment['role'] == role]
            
            if not role_engineers or not all_qualifications[role]:
                continue
            
            role_quals = all_qualifications[role].copy()
            random.shuffle(role_quals)  # Randomize for fairness
            
            # Round-robin distribution with balance enforcement
            qual_index = 0
            rounds = 0
            max_rounds = 10  # Prevent infinite loops
            
            while qual_index < len(role_quals) and rounds < max_rounds:
                # Sort engineers by current qualification count (maintains balance)
                role_engineers.sort(key=lambda e: len(engineer_assignments[e]['qualifications']))
                
                for engineer_id in role_engineers:
                    if qual_index >= len(role_quals):
                        break
                    
                    assignment = engineer_assignments[engineer_id]
                    qual = role_quals[qual_index]
                    
                    # Check if engineer can take this qualification
                    if (len(assignment['qualifications']) < assignment['max_qualifications'] and
                        qual not in assignment['qualifications']):
                        
                        assignment['qualifications'].append(qual)
                        
                        # Track if it's a daily qualification
                        if self._is_daily_qualification(qual, team):
                            assignment['daily_qualifications'].append(qual)
                        
                        qual_index += 1
                
                rounds += 1
        
        # Display distribution
        for role in ['electrical', 'mechanical']:
            role_engineers = [eng_id for eng_id, assignment in engineer_assignments.items() 
                            if assignment['role'] == role]
            
            if role_engineers:
                qual_counts = [len(engineer_assignments[eng]['qualifications']) for eng in role_engineers]
                if qual_counts:
                    avg_quals = sum(qual_counts) / len(qual_counts)
                    min_quals = min(qual_counts)
                    max_quals = max(qual_counts)
                    balance_ratio = min_quals / max_quals if max_quals > 0 else 1
                    
                    print(f"      {role.title()}: {min_quals}-{max_quals} qualifications (avg: {avg_quals:.1f}, balance: {balance_ratio:.2f})")
    
    def _is_daily_qualification(self, qualification_code, team):
        """Check if a qualification is required for daily PPMs"""
        team_rides = [rid for rid, info in self.optimizer.rides_info.items() 
                     if info.get('team_responsible') == team]
        
        for ride_id in team_rides:
            if ride_id in self.optimizer.ppms_by_type['daily']:
                ppm_data = self.optimizer.ppms_by_type['daily'][ride_id]
                for ppm in ppm_data['ppms']:
                    if ppm['qualification_code'] == qualification_code:
                        return True
        return False
    
    def _ensure_shift_window_coverage(self, engineer_assignments, team):
        """Ensure adequate coverage during shift windows with balance in mind"""
        print(f"\n   ⏰ ENSURING SHIFT WINDOW COVERAGE:")
        
        # Check daily PPM coverage during 6-9 AM window
        daily_coverage_gaps = self._identify_daily_coverage_gaps(engineer_assignments, team)
        
        if daily_coverage_gaps:
            print(f"      🔧 Fixing {len(daily_coverage_gaps)} daily coverage gaps while maintaining balance...")
            self._fix_daily_coverage_gaps_balanced(engineer_assignments, daily_coverage_gaps, team)
        else:
            print(f"      ✅ Daily shift window coverage looks good")
        
        # Ensure weekly and monthly coverage
        self._ensure_weekly_monthly_coverage_balanced(engineer_assignments, team)
    
    def _identify_daily_coverage_gaps(self, engineer_assignments, team):
        """Identify gaps in daily PPM coverage during AM shifts"""
        gaps = []
        
        # Get engineers with good early shift ratios
        early_shift_engineers = {'electrical': [], 'mechanical': []}
        
        for engineer_id, assignment in engineer_assignments.items():
            if assignment['early_ratio'] > 0.25:  # At least 25% early shifts
                early_shift_engineers[assignment['role']].append(engineer_id)
        
        # Check each daily PPM for adequate coverage
        team_rides = [rid for rid, info in self.optimizer.rides_info.items() 
                     if info.get('team_responsible') == team]
        
        for ride_id in team_rides:
            if ride_id in self.optimizer.ppms_by_type['daily']:
                ppm_data = self.optimizer.ppms_by_type['daily'][ride_id]
                
                for ppm in ppm_data['ppms']:
                    role = 'electrical' if ppm['maintenance_type'] == 'ELECTRICAL' else 'mechanical'
                    qual_code = ppm['qualification_code']
                    
                    # Count qualified engineers with good early shift availability
                    qualified_early_engineers = []
                    for eng_id in early_shift_engineers[role]:
                        if qual_code in engineer_assignments[eng_id]['qualifications']:
                            qualified_early_engineers.append(eng_id)
                    
                    # Need at least 2 qualified engineers with early shifts for reliability
                    if len(qualified_early_engineers) < 2:
                        gaps.append({
                            'ride_id': ride_id,
                            'ppm_code': ppm['ppm_code'],
                            'qualification_code': qual_code,
                            'maintenance_type': ppm['maintenance_type'],
                            'role': role,
                            'current_coverage': len(qualified_early_engineers),
                            'needed': 2 - len(qualified_early_engineers)
                        })
        
        return gaps
    
    def _fix_daily_coverage_gaps_balanced(self, engineer_assignments, gaps, team):
        """Fix daily coverage gaps while maintaining balanced distribution"""
        for gap in gaps:
            role = gap['role']
            qual_code = gap['qualification_code']
            needed = gap['needed']
            
            # Find engineers who can take this qualification while maintaining balance
            candidates = []
            
            for engineer_id, assignment in engineer_assignments.items():
                if (assignment['role'] == role and
                    assignment['early_ratio'] > 0.15 and  # Some early shifts
                    qual_code not in assignment['qualifications'] and
                    len(assignment['qualifications']) < assignment['max_qualifications']):
                    
                    candidates.append({
                        'engineer_id': engineer_id,
                        'early_ratio': assignment['early_ratio'],
                        'qual_count': len(assignment['qualifications']),
                        'balance_score': assignment['max_qualifications'] - len(assignment['qualifications'])
                    })
            
            # Sort by balance (prefer engineers with fewer qualifications) then by early shift availability
            candidates.sort(key=lambda x: (-x['balance_score'], -x['early_ratio']))
            
            # Add qualification to best balanced candidates
            added = 0
            for candidate in candidates:
                if added >= needed:
                    break
                
                engineer_id = candidate['engineer_id']
                engineer_assignments[engineer_id]['qualifications'].append(qual_code)
                engineer_assignments[engineer_id]['daily_qualifications'].append(qual_code)
                
                print(f"         Added {qual_code} to {engineer_id} (balance maintained)")
                added += 1
    
    def _ensure_weekly_monthly_coverage_balanced(self, engineer_assignments, team):
        """Ensure all weekly and monthly qualifications are covered with balance"""
        print(f"      📅 Checking weekly/monthly coverage with balance...")
        
        # Get all required qualifications
        team_rides = [rid for rid, info in self.optimizer.rides_info.items() 
                     if info.get('team_responsible') == team]
        
        required_quals = {'electrical': set(), 'mechanical': set()}
        assigned_quals = {'electrical': set(), 'mechanical': set()}
        
        # Collect required qualifications
        for ride_id in team_rides:
            for ppm_type in ['weekly', 'monthly']:
                if ride_id in self.optimizer.ppms_by_type[ppm_type]:
                    ppm_data = self.optimizer.ppms_by_type[ppm_type][ride_id]
                    for ppm in ppm_data['ppms']:
                        role = 'electrical' if ppm['maintenance_type'] == 'ELECTRICAL' else 'mechanical'
                        required_quals[role].add(ppm['qualification_code'])
        
        # Collect assigned qualifications
        for engineer_id, assignment in engineer_assignments.items():
            role = assignment['role']
            assigned_quals[role].update(assignment['qualifications'])
        
        # Find and fix missing qualifications with balance in mind
        for role in ['electrical', 'mechanical']:
            missing_quals = required_quals[role] - assigned_quals[role]
            
            if missing_quals:
                print(f"         🔧 Adding {len(missing_quals)} missing {role} qualifications (balanced)...")
                
                # Find engineers with capacity, prioritizing those with fewer qualifications
                role_engineers = [(eng_id, assignment) for eng_id, assignment in engineer_assignments.items() 
                                if assignment['role'] == role and 
                                   len(assignment['qualifications']) < assignment['max_qualifications']]
                
                # Sort by current qualification count (prefer those with fewer for balance)
                role_engineers.sort(key=lambda x: len(x[1]['qualifications']))
                
                # Distribute missing qualifications
                missing_list = list(missing_quals)
                random.shuffle(missing_list)  # Randomize order
                
                for qual in missing_list:
                    if role_engineers:
                        engineer_id, assignment = role_engineers[0]
                        assignment['qualifications'].append(qual)
                        
                        # Re-sort to maintain balance
                        role_engineers.sort(key=lambda x: len(x[1]['qualifications']))
    
    def _balance_and_validate(self, engineer_assignments, team):
        """Final balancing and validation"""
        print(f"\n   ⚖️  FINAL BALANCING AND VALIDATION:")
        
        # Create temporary matrices for validation
        temp_matrices = {team: engineer_assignments}
        
        # Run validation
        validation_results = self.coverage_validator.validate_assignment_coverage(temp_matrices)
        team_results = validation_results[team]
        
        daily_coverage = team_results['daily']['coverage_percentage']
        weekly_coverage = team_results['weekly']['coverage_percentage']
        monthly_coverage = team_results['monthly']['coverage_percentage']
        
        print(f"      📊 Coverage Results:")
        print(f"         Daily: {daily_coverage:.1f}%")
        print(f"         Weekly: {weekly_coverage:.1f}%")
        print(f"         Monthly: {monthly_coverage:.1f}%")
        
        # Final balance check
        self._final_balance_check(engineer_assignments)
        
        return engineer_assignments
    
    def _final_balance_check(self, engineer_assignments):
        """Check final balance and adjust if needed"""
        print(f"      📊 Final Balance Check:")
        
        for role in ['electrical', 'mechanical']:
            role_engineers = [eng_id for eng_id, assignment in engineer_assignments.items() 
                            if assignment['role'] == role]
            
            if not role_engineers:
                continue
            
            qual_counts = [len(engineer_assignments[eng]['qualifications']) for eng in role_engineers]
            
            min_quals = min(qual_counts)
            max_quals = max(qual_counts)
            avg_quals = sum(qual_counts) / len(qual_counts)
            balance_ratio = min_quals / max_quals if max_quals > 0 else 1
            
            print(f"         {role.title()}: {min_quals}-{max_quals} qualifications (avg: {avg_quals:.1f}, balance: {balance_ratio:.2f})")
            
            # Good balance if ratio > 0.7 (minimum is at least 70% of maximum)
            if balance_ratio > 0.7:
                print(f"            ✅ Well balanced")
            elif balance_ratio > 0.5:
                print(f"            ⚖️  Reasonably balanced")
            else:
                print(f"            ⚠️  Could be more balanced")
    
    def _display_balanced_summary(self, engineer_assignments, team):
        """Display balanced assignment summary"""
        print(f"\n   📋 TEAM {team} BALANCED ASSIGNMENT SUMMARY:")
        
        # Group by role
        for role in ['electrical', 'mechanical']:
            role_engineers = [(eng_id, assignment) for eng_id, assignment in engineer_assignments.items() 
                            if assignment['role'] == role]
            
            if not role_engineers:
                continue
            
            print(f"\n      👥 {role.upper()} ENGINEERS ({len(role_engineers)} total):")
            
            # Sort by qualification count for display
            role_engineers.sort(key=lambda x: len(x[1]['qualifications']))
            
            for engineer_id, assignment in role_engineers:
                name = assignment['name']
                rota = assignment['rota_number']
                
                total_quals = len(assignment['qualifications'])
                daily_quals = len(assignment['daily_qualifications'])
                early_ratio = assignment['early_ratio']
                
                print(f"         {engineer_id} ({name}): {total_quals} total ({daily_quals} daily), {early_ratio:.1%} early shifts")
    
    def validate_and_export_results(self, matrices):
        """Validate results using coverage validator"""
        print("\n🧪 VALIDATING BALANCED RESULTS")
        print("=" * 70)
        
        # Run coverage validation
        validation_results = self.coverage_validator.validate_assignment_coverage(matrices)
        
        return validation_results


def main():
    """Run balanced coverage qualification design"""
    print("Balanced Coverage Qualification Designer")
    print("Requires PPM data to be loaded first")


if __name__ == "__main__":
    main() 