#!/usr/bin/env python3

"""
Training Optimization Designer
==============================

This module analyzes current engineer qualifications against optimal requirements
and uses optimization techniques to recommend training that maximizes coverage
improvement while minimizing training effort.

Key Features:
- Loads current qualifications from EngQual.csv
- Compares against optimal MILP-generated matrices
- Identifies critical skill gaps
- Optimizes training assignments for maximum coverage impact
- Provides cost-benefit analysis of training recommendations
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime, timedelta
try:
    import pulp
    PULP_AVAILABLE = True
except ImportError:
    PULP_AVAILABLE = False

from .milp_optimization_designer import MILPOptimizationDesigner
from .coverage_validator import CoverageValidator


class TrainingOptimizationDesigner:
    """Training optimization using current vs optimal state analysis"""
    
    def __init__(self, optimizer_results):
        """Initialize with PPM optimization results"""
        self.optimizer = optimizer_results
        self.milp_designer = MILPOptimizationDesigner(optimizer_results)
        self.coverage_validator = CoverageValidator()
        self.current_date = datetime.now()
        
        print("🎓 TRAINING OPTIMIZATION DESIGNER INITIALIZED")
        print("   Approach: Current state vs optimal training analysis")
        print("   Goal: Maximize coverage improvement with minimal training effort")
        print("   Data: EngQual.csv current qualifications vs MILP optimal state")
    
    def load_current_qualification_state(self):
        """Load current engineer qualifications from EngQual.csv"""
        print("\n📊 LOADING CURRENT QUALIFICATION STATE FROM ENGQUAL.CSV")
        
        try:
            # Load EngQual.csv
            df = pd.read_csv('data/raw/EngQual.csv')
            print(f"   📁 Loaded {len(df)} qualification records")
            
            # Filter for active qualifications (not expired, not temp disqualified)
            current_date = self.current_date
            
            # Convert date columns
            df['Qualification Start'] = pd.to_datetime(df['Qualification Start'], errors='coerce')
            df['Expiration'] = pd.to_datetime(df['Expiration'], errors='coerce')
            
            # Filter active qualifications
            active_mask = (
                (df['Expiration'] > current_date) &  # Not expired
                (df['Temp Disqualified'] != '+') &   # Not temp disqualified
                (df['Employee Name'] != 'OUT OF SERVICE')  # Not out of service
            )
            
            active_df = df[active_mask].copy()
            print(f"   ✅ {len(active_df)} active qualifications")
            
            # Build current qualification matrices by team
            current_matrices = {}
            
            # Load engineer data to get team assignments
            engineers_by_team = self._load_engineer_team_assignments()
            
            for team in [1, 2]:
                current_matrices[team] = {}
                team_engineers = engineers_by_team[team]
                
                for eng_code in team_engineers:
                    eng_name = team_engineers[eng_code]['name']
                    eng_role = team_engineers[eng_code]['role']
                    
                    # Get current qualifications for this engineer
                    eng_quals = active_df[active_df['Employee Code'] == eng_code]['Qualification'].tolist()
                    
                    # Filter to PPM-relevant qualifications only
                    ppm_quals = [q for q in eng_quals if self._is_ppm_qualification(q)]
                    daily_quals = [q for q in ppm_quals if self._is_daily_qualification(q, team)]
                    
                    # Extract ride assignments from qualifications
                    assigned_rides = list(set([q.split('.')[0] for q in ppm_quals]))
                    
                    # Categorize by ride type
                    type_a_rides = [r for r in assigned_rides if self._get_ride_type(r) == 'A']
                    type_b_rides = [r for r in assigned_rides if self._get_ride_type(r) == 'B']
                    type_c_rides = [r for r in assigned_rides if self._get_ride_type(r) == 'C']
                    
                    current_matrices[team][eng_code] = {
                        'name': eng_name,
                        'role': eng_role,
                        'rota_number': team_engineers[eng_code].get('rota_number', 1),
                        'assigned_rides': assigned_rides,
                        'type_a_rides': type_a_rides,
                        'type_b_rides': type_b_rides,
                        'type_c_rides': type_c_rides,
                        'qualifications': ppm_quals,
                        'daily_qualifications': daily_quals,
                        'coverage_score': len(ppm_quals),
                        'current_state': True  # Flag to indicate this is current state
                    }
                
                print(f"   🏢 Team {team}: {len(current_matrices[team])} engineers with qualifications")
            
            return current_matrices
            
        except FileNotFoundError:
            print("   ⚠️  EngQual.csv not found in data/raw/")
            return {}
        except Exception as e:
            print(f"   ❌ Error loading qualifications: {e}")
            return {}
    
    def create_current_state_matrices(self, current_matrices):
        """Convert current qualifications into proper qualification matrices format"""
        print("\n🎯 CREATING QUALIFICATION MATRICES FROM CURRENT STATE")
        
        # The current_matrices from load_current_qualification_state() are already in the right format
        # We just need to ensure they're properly structured for the validation system
        
        formatted_matrices = {}
        
        for team in [1, 2]:
            if team not in current_matrices:
                continue
                
            formatted_matrices[team] = {}
            
            for eng_code, eng_data in current_matrices[team].items():
                # Ensure the engineer data has all required fields for validation
                formatted_matrices[team][eng_code] = {
                    'name': eng_data['name'],
                    'role': eng_data['role'],
                    'rota_number': eng_data.get('rota_number', 1),
                    'assigned_rides': eng_data['assigned_rides'],
                    'type_a_rides': eng_data['type_a_rides'],
                    'type_b_rides': eng_data['type_b_rides'],
                    'type_c_rides': eng_data['type_c_rides'],
                    'qualifications': eng_data['qualifications'],
                    'daily_qualifications': eng_data.get('daily_qualifications', []),
                    'coverage_score': eng_data.get('coverage_score', len(eng_data['qualifications'])),
                    'current_state': True
                }
        
        for team in formatted_matrices:
            print(f"   🏢 Team {team}: {len(formatted_matrices[team])} engineers with current qualifications")
            
        return formatted_matrices
    
    def optimize_training_assignments(self, current_matrices):
        """Generate ride assignments and complete qualification requirements from current state"""
        print("\n🧠 OPTIMIZING TRAINING ASSIGNMENTS FROM CURRENT STATE")
        print("Approach: Assign rides to engineers, then determine ALL required qualifications")
        print("=" * 70)
        
        training_recommendations = {}
        
        for team in [1, 2]:
            if team not in current_matrices:
                continue
                
            print(f"\n🏢 TEAM {team} RIDE ASSIGNMENT & QUALIFICATION ANALYSIS:")
            
            # Step 1: Use MILP designer to get optimal ride assignments
            optimal_ride_assignments = self._get_milp_ride_assignments(team)
            
            # Step 2: For each engineer, determine what qualifications they need for their assigned rides
            qualification_requirements = self._determine_qualification_requirements(
                optimal_ride_assignments, team
            )
            
            # Step 3: Compare current qualifications vs required qualifications
            training_gaps = self._compare_current_vs_required(
                current_matrices[team], qualification_requirements, team
            )
            
            # Step 4: Generate training recommendations for the gaps
            optimized_recommendations = self._generate_training_recommendations(
                training_gaps, team
            )
            
            training_recommendations[team] = optimized_recommendations
        
        return training_recommendations
    
    def _get_milp_ride_assignments(self, team):
        """Get optimal ride assignments from MILP designer"""
        print(f"   🎯 Getting optimal ride assignments for Team {team} from MILP...")
        
        # Use the MILP designer to get optimal assignments
        optimal_matrices = self.milp_designer.create_optimized_qualification_matrices()
        
        if team not in optimal_matrices:
            return {}
        
        ride_assignments = {}
        for eng_code, eng_data in optimal_matrices[team].items():
            ride_assignments[eng_code] = {
                'name': eng_data['name'],
                'role': eng_data['role'],
                'assigned_rides': eng_data['assigned_rides'],
                'type_a_rides': eng_data['type_a_rides'],
                'type_b_rides': eng_data['type_b_rides'],
                'type_c_rides': eng_data['type_c_rides']
            }
        
        print(f"      ✅ Got ride assignments for {len(ride_assignments)} engineers")
        return ride_assignments
    
    def _determine_qualification_requirements(self, ride_assignments, team):
        """Determine ALL qualifications needed for each engineer's assigned rides"""
        print(f"   📋 Determining qualification requirements for assigned rides...")
        
        qualification_requirements = {}
        
        for eng_code, assignment in ride_assignments.items():
            required_quals = set()
            
            # For each assigned ride, get ALL required qualifications
            for ride_code in assignment['assigned_rides']:
                # Get daily qualifications for this ride
                if ride_code in self.optimizer.ppms_by_type['daily']:
                    for ppm in self.optimizer.ppms_by_type['daily'][ride_code]['ppms']:
                        # Check if this qualification matches the engineer's role
                        qual_role = self._get_qualification_role(ppm['qualification_code'])
                        if qual_role == 'any' or assignment['role'] == qual_role:
                            required_quals.add(ppm['qualification_code'])
                
                # Get weekly qualifications for this ride
                if ride_code in self.optimizer.ppms_by_type['weekly']:
                    for ppm in self.optimizer.ppms_by_type['weekly'][ride_code]['ppms']:
                        qual_role = self._get_qualification_role(ppm['qualification_code'])
                        if qual_role == 'any' or assignment['role'] == qual_role:
                            required_quals.add(ppm['qualification_code'])
                
                # Get monthly qualifications for this ride
                if ride_code in self.optimizer.ppms_by_type['monthly']:
                    for ppm in self.optimizer.ppms_by_type['monthly'][ride_code]['ppms']:
                        qual_role = self._get_qualification_role(ppm['qualification_code'])
                        if qual_role == 'any' or assignment['role'] == qual_role:
                            required_quals.add(ppm['qualification_code'])
            
            qualification_requirements[eng_code] = {
                'name': assignment['name'],
                'role': assignment['role'],
                'assigned_rides': assignment['assigned_rides'],
                'required_qualifications': list(required_quals),
                'total_required': len(required_quals)
            }
        
        print(f"      ✅ Determined qualification requirements for {len(qualification_requirements)} engineers")
        return qualification_requirements
    
    def _compare_current_vs_required(self, current_team, qualification_requirements, team):
        """Compare current qualifications vs required qualifications"""
        print(f"   🔍 Comparing current vs required qualifications...")
        
        training_gaps = {}
        
        for eng_code, requirements in qualification_requirements.items():
            # Get current qualifications (if engineer exists)
            current_quals = set()
            if eng_code in current_team:
                current_quals = set(current_team[eng_code]['qualifications'])
            
            # Calculate gaps
            required_quals = set(requirements['required_qualifications'])
            missing_quals = required_quals - current_quals
            
            if missing_quals:
                # Categorize missing qualifications
                daily_missing = [q for q in missing_quals if self._is_daily_qualification(q, team)]
                weekly_missing = [q for q in missing_quals if self._is_weekly_qualification(q, team)]
                monthly_missing = [q for q in missing_quals if self._is_monthly_qualification(q, team)]
                
                training_gaps[eng_code] = {
                    'name': requirements['name'],
                    'role': requirements['role'],
                    'assigned_rides': requirements['assigned_rides'],
                    'current_qualifications': len(current_quals),
                    'required_qualifications': len(required_quals),
                    'missing_qualifications': list(missing_quals),
                    'daily_missing': daily_missing,
                    'weekly_missing': weekly_missing,
                    'monthly_missing': monthly_missing,
                    'total_missing': len(missing_quals),
                    'is_vacancy': eng_code.startswith('VACANCY') or eng_code not in current_team
                }
        
        # Display summary
        total_engineers = len(training_gaps)
        vacancy_engineers = len([gap for gap in training_gaps.values() if gap['is_vacancy']])
        real_engineers = total_engineers - vacancy_engineers
        
        print(f"      📊 Training gap summary:")
        print(f"         Real engineers needing training: {real_engineers}")
        print(f"         Vacant positions needing qualifications: {vacancy_engineers}")
        print(f"         Total positions: {total_engineers}")
        
        # Show top gaps
        sorted_gaps = sorted(training_gaps.items(), key=lambda x: x[1]['total_missing'], reverse=True)
        print(f"      🎯 Top 3 training priorities:")
        for i, (eng_code, gap) in enumerate(sorted_gaps[:3]):
            status = "VACANT" if gap['is_vacancy'] else "CURRENT"
            print(f"         {i+1}. {gap['name']} ({status}): {gap['total_missing']} quals needed")
        
        return training_gaps
    
    def _generate_training_recommendations(self, training_gaps, team):
        """Generate training recommendations from training gaps"""
        print(f"   💡 Generating training recommendations...")
        
        optimized_assignments = []
        
        for eng_code, gap in training_gaps.items():
            # For all engineers (including vacancies), recommend all missing qualifications
            if gap['missing_qualifications']:
                optimized_assignments.append({
                    'engineer_code': eng_code,
                    'engineer_name': gap['name'],
                    'role': gap['role'],
                    'assigned_rides': gap['assigned_rides'],
                    'recommended_qualifications': gap['missing_qualifications'],
                    'training_effort': gap['total_missing'],
                    'daily_impact': len(gap['daily_missing']),
                    'weekly_impact': len(gap['weekly_missing']),
                    'monthly_impact': len(gap['monthly_missing']),
                    'is_vacancy': gap['is_vacancy']
                })
        
        # Sort by training effort (vacancies typically need more)
        optimized_assignments.sort(key=lambda x: x['training_effort'], reverse=True)
        
        total_effort = sum(a['training_effort'] for a in optimized_assignments)
        vacancy_effort = sum(a['training_effort'] for a in optimized_assignments if a['is_vacancy'])
        
        print(f"      ✅ Generated recommendations for {len(optimized_assignments)} engineers")
        print(f"      📚 Total training effort: {total_effort} qualifications")
        print(f"      🏢 Vacancy training effort: {vacancy_effort} qualifications")
        
        return {
            'optimized_assignments': optimized_assignments,
            'total_training_effort': total_effort,
            'vacancy_training_effort': vacancy_effort,
            'method': 'MILP_Ride_Assignment'
        }
    
    def generate_detailed_training_report(self, training_recommendations, current_matrices):
        """Generate detailed training report with current vs recommended breakdown"""
        print("\n📊 GENERATING DETAILED TRAINING REPORT")
        print("=" * 70)
        
        detailed_report = {}
        
        for team in [1, 2]:
            if team not in training_recommendations or team not in current_matrices:
                continue
                
            print(f"\n🏢 TEAM {team} DETAILED TRAINING ANALYSIS:")
            
            team_report = {
                'engineers': {},
                'summary': {
                    'total_engineers': 0,
                    'engineers_needing_training': 0,
                    'vacant_positions': 0,
                    'total_training_effort': 0,
                    'high_impact_training': 0,
                    'medium_impact_training': 0,
                    'low_impact_training': 0
                },
                'priority_training': []
            }
            
            team_current = current_matrices[team]
            team_recommendations = training_recommendations[team]['optimized_assignments']
            
            # Create lookup for easy access
            rec_lookup = {rec['engineer_code']: rec for rec in team_recommendations}
            
            for eng_code, current_profile in team_current.items():
                engineer_report = self._generate_engineer_detailed_report(
                    eng_code, current_profile, rec_lookup.get(eng_code), team
                )
                
                if engineer_report:
                    team_report['engineers'][eng_code] = engineer_report
                    
                    # Update summary
                    team_report['summary']['total_engineers'] += 1
                    if engineer_report['needs_training']:
                        team_report['summary']['engineers_needing_training'] += 1
                        team_report['summary']['total_training_effort'] += engineer_report['training_effort']
                        
                        # Categorize impact
                        if engineer_report['daily_impact'] >= 3:
                            team_report['summary']['high_impact_training'] += 1
                        elif engineer_report['daily_impact'] >= 1:
                            team_report['summary']['medium_impact_training'] += 1
                        else:
                            team_report['summary']['low_impact_training'] += 1
                    
                    if engineer_report['is_vacancy']:
                        team_report['summary']['vacant_positions'] += 1
            
            # Generate priority training list
            team_report['priority_training'] = self._generate_priority_training_list(team_report['engineers'])
            
            # Display summary
            summary = team_report['summary']
            print(f"   📈 TEAM {team} SUMMARY:")
            print(f"      Total Engineers: {summary['total_engineers']}")
            print(f"      Need Training: {summary['engineers_needing_training']}")
            print(f"      Vacant Positions: {summary['vacant_positions']}")
            print(f"      Total Training Effort: {summary['total_training_effort']} qualifications")
            print(f"      High Impact Training: {summary['high_impact_training']} engineers (≥3 daily)")
            print(f"      Medium Impact Training: {summary['medium_impact_training']} engineers (1-2 daily)")
            print(f"      Low Impact Training: {summary['low_impact_training']} engineers (0 daily)")
            
            detailed_report[team] = team_report
        
        return detailed_report
    
    def _generate_engineer_detailed_report(self, eng_code, current_profile, recommendation, team):
        """Generate detailed report for individual engineer"""
        if not recommendation:
            return {
                'engineer_code': eng_code,
                'engineer_name': current_profile['name'],
                'role': current_profile['role'],
                'needs_training': False,
                'is_vacancy': eng_code.startswith('VACANCY'),
                'current_total_qualifications': len(current_profile['qualifications']),
                'current_daily_qualifications': len(current_profile['daily_qualifications']),
                'assigned_rides': current_profile.get('assigned_rides', []),
                'ride_breakdown': {},
                'training_effort': 0,
                'daily_impact': 0,
                'weekly_impact': 0,
                'monthly_impact': 0
            }
        
        # Generate ride-by-ride breakdown
        ride_breakdown = {}
        for ride_code in recommendation['assigned_rides']:
            ride_analysis = self._analyze_ride_qualifications(
                ride_code, current_profile['qualifications'], 
                recommendation['recommended_qualifications'], team
            )
            ride_breakdown[ride_code] = ride_analysis
        
        return {
            'engineer_code': eng_code,
            'engineer_name': current_profile['name'],
            'role': current_profile['role'],
            'needs_training': True,
            'is_vacancy': recommendation['is_vacancy'],
            'current_total_qualifications': len(current_profile['qualifications']),
            'current_daily_qualifications': len(current_profile['daily_qualifications']),
            'assigned_rides': recommendation['assigned_rides'],
            'ride_breakdown': ride_breakdown,
            'recommended_qualifications': recommendation['recommended_qualifications'],
            'training_effort': recommendation['training_effort'],
            'daily_impact': recommendation['daily_impact'],
            'weekly_impact': recommendation['weekly_impact'],
            'monthly_impact': recommendation['monthly_impact'],
            'training_priority_score': self._calculate_training_priority_score(recommendation)
        }
    
    def _analyze_ride_qualifications(self, ride_code, current_quals, recommended_quals, team):
        """Analyze qualifications for a specific ride"""
        # Get all possible qualifications for this ride
        ride_quals = {
            'daily': [],
            'weekly': [],
            'monthly': []
        }
        
        # Check daily PPMs
        if ride_code in self.optimizer.ppms_by_type['daily']:
            for ppm in self.optimizer.ppms_by_type['daily'][ride_code]['ppms']:
                ride_quals['daily'].append(ppm['qualification_code'])
        
        # Check weekly PPMs
        if ride_code in self.optimizer.ppms_by_type['weekly']:
            for ppm in self.optimizer.ppms_by_type['weekly'][ride_code]['ppms']:
                ride_quals['weekly'].append(ppm['qualification_code'])
        
        # Check monthly PPMs
        if ride_code in self.optimizer.ppms_by_type['monthly']:
            for ppm in self.optimizer.ppms_by_type['monthly'][ride_code]['ppms']:
                ride_quals['monthly'].append(ppm['qualification_code'])
        
        # Analyze current vs required
        all_ride_quals = ride_quals['daily'] + ride_quals['weekly'] + ride_quals['monthly']
        current_ride_quals = [q for q in current_quals if q.startswith(ride_code + '.')]
        recommended_ride_quals = [q for q in recommended_quals if q.startswith(ride_code + '.')]
        
        return {
            'ride_code': ride_code,
            'ride_type': self._get_ride_type(ride_code),
            'total_possible_qualifications': len(all_ride_quals),
            'current_qualifications': current_ride_quals,
            'current_count': len(current_ride_quals),
            'recommended_additional': recommended_ride_quals,
            'recommended_count': len(recommended_ride_quals),
            'final_count': len(current_ride_quals) + len(recommended_ride_quals),
            'daily_qualifications': {
                'current': [q for q in current_ride_quals if q in ride_quals['daily']],
                'recommended': [q for q in recommended_ride_quals if q in ride_quals['daily']]
            },
            'weekly_qualifications': {
                'current': [q for q in current_ride_quals if q in ride_quals['weekly']],
                'recommended': [q for q in recommended_ride_quals if q in ride_quals['weekly']]
            },
            'monthly_qualifications': {
                'current': [q for q in current_ride_quals if q in ride_quals['monthly']],
                'recommended': [q for q in recommended_ride_quals if q in ride_quals['monthly']]
            }
        }
    
    def _calculate_training_priority_score(self, recommendation):
        """Calculate priority score for training (higher = more important)"""
        # Priority factors:
        # Daily impact: 10 points per daily qualification
        # Weekly impact: 5 points per weekly qualification  
        # Monthly impact: 2 points per monthly qualification
        # Vacancy penalty: -20 points (lower priority than current staff)
        
        score = (recommendation['daily_impact'] * 10 + 
                recommendation['weekly_impact'] * 5 + 
                recommendation['monthly_impact'] * 2)
        
        if recommendation['is_vacancy']:
            score -= 20  # Lower priority for vacant positions
            
        return score
    
    def _generate_priority_training_list(self, engineers_report):
        """Generate prioritized training list"""
        # Get engineers needing training and sort by priority
        training_engineers = [
            eng for eng in engineers_report.values() 
            if eng['needs_training']
        ]
        
        # Sort by priority score (high to low)
        training_engineers.sort(key=lambda x: x['training_priority_score'], reverse=True)
        
        priority_list = []
        for i, eng in enumerate(training_engineers[:10]):  # Top 10
            priority_item = {
                'rank': i + 1,
                'engineer_code': eng['engineer_code'],
                'engineer_name': eng['engineer_name'],
                'is_vacancy': eng['is_vacancy'],
                'training_effort': eng['training_effort'],
                'daily_impact': eng['daily_impact'],
                'priority_score': eng['training_priority_score'],
                'top_rides_needing_training': []
            }
            
            # Get top 3 rides with most training needed
            ride_training_needs = []
            for ride_code, ride_data in eng['ride_breakdown'].items():
                if ride_data['recommended_count'] > 0:
                    ride_training_needs.append({
                        'ride_code': ride_code,
                        'ride_type': ride_data['ride_type'],
                        'training_needed': ride_data['recommended_count'],
                        'daily_training': len(ride_data['daily_qualifications']['recommended'])
                    })
            
            ride_training_needs.sort(key=lambda x: (x['daily_training'], x['training_needed']), reverse=True)
            priority_item['top_rides_needing_training'] = ride_training_needs[:3]
            
            priority_list.append(priority_item)
        
        return priority_list
    
    def display_detailed_training_report(self, detailed_report):
        """Display the detailed training report in a readable format"""
        print("\n📋 DETAILED TRAINING ANALYSIS REPORT")
        print("=" * 80)
        
        for team, team_data in detailed_report.items():
            print(f"\n🏢 TEAM {team} DETAILED BREAKDOWN:")
            print("-" * 50)
            
            # Show priority training first
            print(f"\n🎯 TOP TRAINING PRIORITIES:")
            for priority in team_data['priority_training'][:5]:  # Top 5
                status = "VACANT" if priority['is_vacancy'] else "CURRENT"
                print(f"   {priority['rank']}. {priority['engineer_name']} ({status})")
                print(f"      📚 Training Effort: {priority['training_effort']} qualifications")
                print(f"      🌅 Daily Impact: {priority['daily_impact']} qualifications")
                print(f"      🎯 Priority Score: {priority['priority_score']}")
                print(f"      🎢 Top Rides Needing Training:")
                for ride in priority['top_rides_needing_training']:
                    print(f"         - {ride['ride_code']} (Type {ride['ride_type']}): {ride['training_needed']} quals ({ride['daily_training']} daily)")
                print()
            
            # Show detailed breakdown for top engineers
            print(f"\n📊 DETAILED ENGINEER BREAKDOWN (Top 3):")
            top_engineers = sorted(
                [eng for eng in team_data['engineers'].values() if eng['needs_training']], 
                key=lambda x: x['training_priority_score'], reverse=True
            )[:3]
            
            for eng in top_engineers:
                self._display_engineer_breakdown(eng)
    
    def _display_engineer_breakdown(self, engineer_report):
        """Display detailed breakdown for individual engineer"""
        status = "VACANT" if engineer_report['is_vacancy'] else "CURRENT"
        print(f"\n   👤 {engineer_report['engineer_name']} ({status}) - {engineer_report['role'].upper()}")
        print(f"      Current Qualifications: {engineer_report['current_total_qualifications']} total, {engineer_report['current_daily_qualifications']} daily")
        print(f"      Training Needed: {engineer_report['training_effort']} qualifications")
        print(f"      Impact: {engineer_report['daily_impact']} daily, {engineer_report['weekly_impact']} weekly, {engineer_report['monthly_impact']} monthly")
        print(f"      Assigned Rides: {', '.join(engineer_report['assigned_rides'])}")
        
        print(f"      🎢 RIDE-BY-RIDE BREAKDOWN:")
        for ride_code, ride_data in engineer_report['ride_breakdown'].items():
            if ride_data['recommended_count'] > 0:
                current_count = ride_data['current_count']
                recommended_count = ride_data['recommended_count']
                final_count = ride_data['final_count']
                
                print(f"         {ride_code} (Type {ride_data['ride_type']}): {current_count} → {final_count} (+{recommended_count})")
                
                # Show daily qualifications breakdown
                daily_current = len(ride_data['daily_qualifications']['current'])
                daily_recommended = len(ride_data['daily_qualifications']['recommended'])
                if daily_recommended > 0:
                    print(f"           🌅 Daily: {daily_current} → {daily_current + daily_recommended} (+{daily_recommended})")
                
                # Show weekly qualifications breakdown
                weekly_current = len(ride_data['weekly_qualifications']['current'])
                weekly_recommended = len(ride_data['weekly_qualifications']['recommended'])
                if weekly_recommended > 0:
                    print(f"           📅 Weekly: {weekly_current} → {weekly_current + weekly_recommended} (+{weekly_recommended})")
                
                # Show monthly qualifications breakdown
                monthly_current = len(ride_data['monthly_qualifications']['current'])
                monthly_recommended = len(ride_data['monthly_qualifications']['recommended'])
                if monthly_recommended > 0:
                    print(f"           📆 Monthly: {monthly_current} → {monthly_current + monthly_recommended} (+{monthly_recommended})")
        
        print()
        
    def export_detailed_report_to_csv(self, detailed_report, output_dir="outputs/current"):
        """Export detailed training report to CSV files for easy analysis"""
        import csv
        import os
        from pathlib import Path
        
        print(f"\n📊 EXPORTING DETAILED TRAINING REPORT TO CSV")
        print("=" * 60)
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Create comprehensive engineer summary CSV
        summary_file = output_path / "training_summary_by_engineer.csv"
        print(f"   📄 Creating engineer summary: {summary_file}")
        
        with open(summary_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header row
            writer.writerow([
                'Team', 'Engineer_Code', 'Engineer_Name', 'Role', 'Status',
                'Current_Total_Quals', 'Current_Daily_Quals', 'Training_Effort',
                'Daily_Impact', 'Weekly_Impact', 'Monthly_Impact', 'Priority_Score',
                'Assigned_Rides', 'Rides_Count', 'Type_A_Rides', 'Type_B_Rides', 'Type_C_Rides'
            ])
            
            # Data rows
            for team, team_data in detailed_report.items():
                for eng_code, eng_data in team_data['engineers'].items():
                    if eng_data['needs_training']:
                        # Count ride types
                        type_a_rides = [r for r in eng_data['assigned_rides'] 
                                      if eng_data['ride_breakdown'][r]['ride_type'] == 'A']
                        type_b_rides = [r for r in eng_data['assigned_rides'] 
                                      if eng_data['ride_breakdown'][r]['ride_type'] == 'B']
                        type_c_rides = [r for r in eng_data['assigned_rides'] 
                                      if eng_data['ride_breakdown'][r]['ride_type'] == 'C']
                        
                        writer.writerow([
                            team,
                            eng_data['engineer_code'],
                            eng_data['engineer_name'],
                            eng_data['role'].title(),
                            'VACANT' if eng_data['is_vacancy'] else 'CURRENT',
                            eng_data['current_total_qualifications'],
                            eng_data['current_daily_qualifications'],
                            eng_data['training_effort'],
                            eng_data['daily_impact'],
                            eng_data['weekly_impact'],
                            eng_data['monthly_impact'],
                            eng_data['training_priority_score'],
                            ', '.join(eng_data['assigned_rides']),
                            len(eng_data['assigned_rides']),
                            ', '.join(type_a_rides),
                            ', '.join(type_b_rides),
                            ', '.join(type_c_rides)
                        ])
        
        # Create detailed ride-by-ride breakdown CSV
        rides_file = output_path / "training_breakdown_by_ride.csv"
        print(f"   📄 Creating ride breakdown: {rides_file}")
        
        with open(rides_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header row
            writer.writerow([
                'Team', 'Engineer_Code', 'Engineer_Name', 'Role', 'Status',
                'Ride_Code', 'Ride_Type', 'Current_Quals', 'Additional_Needed',
                'Final_Quals', 'Daily_Current', 'Daily_Needed', 'Weekly_Current',
                'Weekly_Needed', 'Monthly_Current', 'Monthly_Needed'
            ])
            
            # Data rows
            for team, team_data in detailed_report.items():
                for eng_code, eng_data in team_data['engineers'].items():
                    if eng_data['needs_training']:
                        for ride_code, ride_data in eng_data['ride_breakdown'].items():
                            if ride_data['recommended_count'] > 0:
                                writer.writerow([
                                    team,
                                    eng_data['engineer_code'],
                                    eng_data['engineer_name'],
                                    eng_data['role'].title(),
                                    'VACANT' if eng_data['is_vacancy'] else 'CURRENT',
                                    ride_code,
                                    ride_data['ride_type'],
                                    ride_data['current_count'],
                                    ride_data['recommended_count'],
                                    ride_data['final_count'],
                                    len(ride_data['daily_qualifications']['current']),
                                    len(ride_data['daily_qualifications']['recommended']),
                                    len(ride_data['weekly_qualifications']['current']),
                                    len(ride_data['weekly_qualifications']['recommended']),
                                    len(ride_data['monthly_qualifications']['current']),
                                    len(ride_data['monthly_qualifications']['recommended'])
                                ])
        
        # Create specific qualifications needed CSV
        quals_file = output_path / "specific_qualifications_needed.csv"
        print(f"   📄 Creating specific qualifications: {quals_file}")
        
        with open(quals_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header row
            writer.writerow([
                'Team', 'Engineer_Code', 'Engineer_Name', 'Role', 'Status',
                'Ride_Code', 'Ride_Type', 'Qualification_Code', 'PPM_Type',
                'Priority_Level'
            ])
            
            # Data rows
            for team, team_data in detailed_report.items():
                for eng_code, eng_data in team_data['engineers'].items():
                    if eng_data['needs_training']:
                        for ride_code, ride_data in eng_data['ride_breakdown'].items():
                            # Daily qualifications (highest priority)
                            for qual in ride_data['daily_qualifications']['recommended']:
                                writer.writerow([
                                    team, eng_data['engineer_code'], eng_data['engineer_name'],
                                    eng_data['role'].title(), 'VACANT' if eng_data['is_vacancy'] else 'CURRENT',
                                    ride_code, ride_data['ride_type'], qual, 'Daily', 'HIGH'
                                ])
                            
                            # Weekly qualifications (medium priority)
                            for qual in ride_data['weekly_qualifications']['recommended']:
                                writer.writerow([
                                    team, eng_data['engineer_code'], eng_data['engineer_name'],
                                    eng_data['role'].title(), 'VACANT' if eng_data['is_vacancy'] else 'CURRENT',
                                    ride_code, ride_data['ride_type'], qual, 'Weekly', 'MEDIUM'
                                ])
                            
                            # Monthly qualifications (lower priority)
                            for qual in ride_data['monthly_qualifications']['recommended']:
                                writer.writerow([
                                    team, eng_data['engineer_code'], eng_data['engineer_name'],
                                    eng_data['role'].title(), 'VACANT' if eng_data['is_vacancy'] else 'CURRENT',
                                    ride_code, ride_data['ride_type'], qual, 'Monthly', 'LOW'
                                ])
        
        # Create priority ranking CSV
        priority_file = output_path / "training_priority_ranking.csv"
        print(f"   📄 Creating priority ranking: {priority_file}")
        
        with open(priority_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header row
            writer.writerow([
                'Overall_Rank', 'Team', 'Engineer_Code', 'Engineer_Name', 'Role', 'Status',
                'Priority_Score', 'Training_Effort', 'Daily_Impact', 'Weekly_Impact', 'Monthly_Impact',
                'Top_Ride_1', 'Top_Ride_1_Type', 'Top_Ride_1_Training', 'Top_Ride_1_Daily',
                'Top_Ride_2', 'Top_Ride_2_Type', 'Top_Ride_2_Training', 'Top_Ride_2_Daily',
                'Top_Ride_3', 'Top_Ride_3_Type', 'Top_Ride_3_Training', 'Top_Ride_3_Daily'
            ])
            
            # Collect all engineers and sort by priority
            all_engineers = []
            for team, team_data in detailed_report.items():
                for priority_item in team_data['priority_training']:
                    eng_data = team_data['engineers'][priority_item['engineer_code']]
                    all_engineers.append({
                        'team': team,
                        'priority_data': priority_item,
                        'eng_data': eng_data
                    })
            
            # Sort by priority score
            all_engineers.sort(key=lambda x: x['priority_data']['priority_score'], reverse=True)
            
            # Write data
            for rank, engineer in enumerate(all_engineers, 1):
                priority_data = engineer['priority_data']
                eng_data = engineer['eng_data']
                
                # Get top 3 rides
                top_rides = priority_data['top_rides_needing_training'][:3]
                
                row = [
                    rank,
                    engineer['team'],
                    priority_data['engineer_code'],
                    priority_data['engineer_name'],
                    eng_data['role'].title(),
                    'VACANT' if priority_data['is_vacancy'] else 'CURRENT',
                    priority_data['priority_score'],
                    priority_data['training_effort'],
                    priority_data['daily_impact'],
                    eng_data['weekly_impact'],
                    eng_data['monthly_impact']
                ]
                
                # Add top 3 rides data
                for i in range(3):
                    if i < len(top_rides):
                        ride = top_rides[i]
                        row.extend([
                            ride['ride_code'],
                            ride['ride_type'],
                            ride['training_needed'],
                            ride['daily_training']
                        ])
                    else:
                        row.extend(['', '', '', ''])
                
                writer.writerow(row)
        
        print(f"   ✅ CSV export completed!")
        print(f"   📁 Files saved to: {output_path}")
        print(f"   📊 Summary: {summary_file.name}")
        print(f"   🎢 Ride breakdown: {rides_file.name}")
        print(f"   📋 Specific qualifications: {quals_file.name}")
        print(f"   🎯 Priority ranking: {priority_file.name}")
        
        return {
            'summary_file': str(summary_file),
            'rides_file': str(rides_file),
            'qualifications_file': str(quals_file),
            'priority_file': str(priority_file)
        }
    
    def validate_training_impact(self, training_recommendations):
        """Validate the impact of proposed training on coverage"""
        print("\n🧪 VALIDATING TRAINING IMPACT ON COVERAGE")
        print("=" * 70)
        
        # Create projected qualification matrices after training
        projected_matrices = self._apply_training_to_current_state(training_recommendations)
        
        # Validate coverage of projected state
        validation_results = self.coverage_validator.validate_assignment_coverage(projected_matrices)
        
        for team in [1, 2]:
            if team in validation_results:
                results = validation_results[team]
                daily_cov = results['daily']['coverage_percentage']
                weekly_cov = results['weekly']['coverage_percentage']
                monthly_cov = results['monthly']['coverage_percentage']
                
                print(f"\n🏢 TEAM {team} POST-TRAINING COVERAGE PROJECTION:")
                print(f"   Daily Coverage:   {daily_cov:.1f}% {'🎯' if daily_cov >= 90 else '⚠️' if daily_cov >= 60 else '❌'}")
                print(f"   Weekly Coverage:  {weekly_cov:.1f}% {'🎯' if weekly_cov >= 90 else '⚠️' if weekly_cov >= 60 else '❌'}")
                print(f"   Monthly Coverage: {monthly_cov:.1f}% {'🎯' if monthly_cov >= 90 else '⚠️' if monthly_cov >= 60 else '❌'}")
        
        return validation_results
    
    def _load_engineer_team_assignments(self):
        """Load engineer team assignments from processed data"""
        engineers_by_team = {1: {}, 2: {}}
        
        for team in [1, 2]:
            for role in ['elec', 'mech']:
                file_path = f'data/processed/engineers/team{team}_{role}_engineers.json'
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        for eng in data.get('engineers', []):
                            eng_code = eng['employee_code']
                            engineers_by_team[team][eng_code] = {
                                'name': eng['timeplan_name'],
                                'role': 'electrical' if role == 'elec' else 'mechanical',
                                'rota_number': eng.get('rota_number', 1),
                                'active': eng.get('active', True),
                                'vacancy': eng.get('vacancy', False)
                            }
                except FileNotFoundError:
                    continue
        
        return engineers_by_team
    
    def _is_ppm_qualification(self, qualification):
        """Check if qualification is PPM-related (format: RIDE.X.TYPE.S)"""
        parts = qualification.split('.')
        if len(parts) < 3:
            return False
        
        # Check if it's a ride code we know about
        ride_code = parts[0]
        return ride_code in self.optimizer.rides_info
    
    def _is_daily_qualification(self, qualification, team):
        """Check if qualification is for daily PPMs"""
        ride_code = qualification.split('.')[0]
        
        if ride_code in self.optimizer.ppms_by_type['daily']:
            ppm_data = self.optimizer.ppms_by_type['daily'][ride_code]
            for ppm in ppm_data['ppms']:
                if ppm['qualification_code'] == qualification:
                    return True
        return False
    
    def _get_ride_type(self, ride_code):
        """Get ride complexity type (A, B, or C)"""
        if ride_code in self.optimizer.rides_info:
            return self.optimizer.rides_info[ride_code].get('type', 'C')
        return 'C'
    
    def _analyze_current_coverage_gaps(self, team_current, team):
        """Analyze coverage gaps in current state"""
        print(f"   📊 Analyzing coverage gaps in current Team {team} state...")
        
        # Get all required qualifications for this team
        all_required_quals = set()
        
        # Get daily qualifications (highest priority)
        for ride_code, ppm_data in self.optimizer.ppms_by_type['daily'].items():
            if ride_code in self.optimizer.rides_info:
                team_responsible = self.optimizer.rides_info[ride_code].get('team_responsible')
                if team_responsible == team:
                    for ppm in ppm_data['ppms']:
                        all_required_quals.add(ppm['qualification_code'])
        
        # Get weekly qualifications
        for ride_code, ppm_data in self.optimizer.ppms_by_type['weekly'].items():
            if ride_code in self.optimizer.rides_info:
                team_responsible = self.optimizer.rides_info[ride_code].get('team_responsible')
                if team_responsible == team:
                    for ppm in ppm_data['ppms']:
                        all_required_quals.add(ppm['qualification_code'])
        
        # Get monthly qualifications
        for ride_code, ppm_data in self.optimizer.ppms_by_type['monthly'].items():
            if ride_code in self.optimizer.rides_info:
                team_responsible = self.optimizer.rides_info[ride_code].get('team_responsible')
                if team_responsible == team:
                    for ppm in ppm_data['ppms']:
                        all_required_quals.add(ppm['qualification_code'])
        
        # Get qualifications currently held by team
        current_quals = set()
        for eng_data in team_current.values():
            current_quals.update(eng_data['qualifications'])
        
        # Identify gaps
        missing_quals = all_required_quals - current_quals
        
        # Categorize gaps by priority
        daily_gaps = [q for q in missing_quals if self._is_daily_qualification(q, team)]
        weekly_gaps = [q for q in missing_quals if self._is_weekly_qualification(q, team)]
        monthly_gaps = [q for q in missing_quals if self._is_monthly_qualification(q, team)]
        
        gaps = {
            'total_required': len(all_required_quals),
            'currently_covered': len(all_required_quals - missing_quals),
            'missing_qualifications': list(missing_quals),
            'daily_gaps': daily_gaps,
            'weekly_gaps': weekly_gaps,
            'monthly_gaps': monthly_gaps,
            'coverage_percentage': ((len(all_required_quals) - len(missing_quals)) / len(all_required_quals)) * 100 if all_required_quals else 100
        }
        
        print(f"      Required qualifications: {gaps['total_required']}")
        print(f"      Currently covered: {gaps['currently_covered']} ({gaps['coverage_percentage']:.1f}%)")
        print(f"      Missing daily PPM quals: {len(gaps['daily_gaps'])}")
        print(f"      Missing weekly PPM quals: {len(gaps['weekly_gaps'])}")
        print(f"      Missing monthly PPM quals: {len(gaps['monthly_gaps'])}")
        
        return gaps
    
    def _is_weekly_qualification(self, qualification, team):
        """Check if qualification is for weekly PPMs"""
        ride_code = qualification.split('.')[0]
        
        if ride_code in self.optimizer.ppms_by_type['weekly']:
            ppm_data = self.optimizer.ppms_by_type['weekly'][ride_code]
            for ppm in ppm_data['ppms']:
                if ppm['qualification_code'] == qualification:
                    return True
        return False
    
    def _is_monthly_qualification(self, qualification, team):
        """Check if qualification is for monthly PPMs"""
        ride_code = qualification.split('.')[0]
        
        if ride_code in self.optimizer.ppms_by_type['monthly']:
            ppm_data = self.optimizer.ppms_by_type['monthly'][ride_code]
            for ppm in ppm_data['ppms']:
                if ppm['qualification_code'] == qualification:
                    return True
        return False
    
    def _optimize_training_for_coverage_gaps(self, team_current, coverage_gaps, team):
        """Use MILP to optimize training to fill coverage gaps"""
        print(f"   🔢 Using MILP to optimize Team {team} training for coverage gaps...")
        
        if not coverage_gaps['missing_qualifications']:
            return {'optimized_assignments': [], 'total_training_effort': 0, 'method': 'MILP'}
        
        # Create MILP problem
        prob = pulp.LpProblem(f"Team_{team}_Coverage_Gap_Training", pulp.LpMinimize)
        
        # Decision variables: train[engineer][qualification] = 1 if we train this engineer on this qual
        train_vars = {}
        total_training_effort = 0
        
        # Only consider engineers who could potentially learn the missing qualifications
        for eng_code, eng_data in team_current.items():
            train_vars[eng_code] = {}
            for qual in coverage_gaps['missing_qualifications']:
                # Check if this engineer's role matches the qualification
                qual_role = self._get_qualification_role(qual)
                if qual_role == 'any' or eng_data['role'] == qual_role:
                    var_name = f"train_{eng_code}_{qual.replace('.', '_')}"
                    train_vars[eng_code][qual] = pulp.LpVariable(var_name, cat='Binary')
                    total_training_effort += train_vars[eng_code][qual]
        
        # Objective: Minimize total training effort
        prob += total_training_effort, "Minimize_Training_Effort"
        
        # Constraints: Ensure each missing qualification is covered by at least one engineer
        for qual in coverage_gaps['missing_qualifications']:
            engineers_who_can_learn = []
            for eng_code in train_vars:
                if qual in train_vars[eng_code]:
                    engineers_who_can_learn.append(eng_code)
            
            if engineers_who_can_learn:
                coverage_sum = pulp.lpSum([
                    train_vars[eng_code][qual] 
                    for eng_code in engineers_who_can_learn
                ])
                
                # Prioritize daily qualifications (require at least 1 person)
                min_coverage = 2 if qual in coverage_gaps['daily_gaps'] else 1
                prob += coverage_sum >= min_coverage, f"Coverage_{qual.replace('.', '_')}"
        
        # Constraint: Limit training load per engineer
        for eng_code in train_vars:
            if train_vars[eng_code]:
                total_quals_for_eng = pulp.lpSum([
                    train_vars[eng_code][qual] 
                    for qual in train_vars[eng_code]
                ])
                prob += total_quals_for_eng <= 8, f"Max_Training_{eng_code}"  # Max 8 new quals per engineer
        
        # Solve
        prob.solve(pulp.PULP_CBC_CMD(msg=0))
        
        # Extract solution
        optimized_assignments = []
        if pulp.LpStatus[prob.status] == 'Optimal':
            for eng_code in train_vars:
                recommended_quals = []
                for qual in train_vars[eng_code]:
                    if train_vars[eng_code][qual].varValue == 1:
                        recommended_quals.append(qual)
                
                if recommended_quals:
                    eng_data = team_current[eng_code]
                    daily_impact = len([q for q in recommended_quals if q in coverage_gaps['daily_gaps']])
                    
                    optimized_assignments.append({
                        'engineer_code': eng_code,
                        'engineer_name': eng_data['name'],
                        'role': eng_data['role'],
                        'recommended_qualifications': recommended_quals,
                        'training_effort': len(recommended_quals),
                        'daily_impact': daily_impact,
                        'coverage_improvement': len(recommended_quals)
                    })
            
            print(f"      ✅ Optimal solution: {len(optimized_assignments)} engineers need training")
            total_effort = sum(a['training_effort'] for a in optimized_assignments)
            daily_coverage = sum(a['daily_impact'] for a in optimized_assignments)
            print(f"      📚 Total training effort: {total_effort} qualifications")
            print(f"      🌅 Daily PPM improvement: {daily_coverage} qualifications")
        else:
            print(f"      ⚠️  No optimal solution found, using heuristic")
            return self._optimize_training_heuristically_for_gaps(team_current, coverage_gaps, team)
        
        return {
            'optimized_assignments': optimized_assignments,
            'total_training_effort': sum(a['training_effort'] for a in optimized_assignments),
            'coverage_improvement': len(coverage_gaps['missing_qualifications']),
            'method': 'MILP'
        }
    
    def _optimize_training_heuristically_for_gaps(self, team_current, coverage_gaps, team):
        """Use heuristic optimization for coverage gaps"""
        print(f"   🧠 Using heuristic optimization for Team {team} coverage gaps...")
        
        optimized_assignments = []
        
        # Prioritize daily gaps first, then weekly, then monthly
        prioritized_gaps = (
            coverage_gaps['daily_gaps'] + 
            coverage_gaps['weekly_gaps'] + 
            coverage_gaps['monthly_gaps']
        )
        
        # Simple heuristic: assign qualifications to engineers with compatible roles
        engineer_loads = {eng_code: 0 for eng_code in team_current.keys()}
        
        for qual in prioritized_gaps:
            qual_role = self._get_qualification_role(qual)
            
            # Find engineers who can learn this qualification
            candidates = []
            for eng_code, eng_data in team_current.items():
                if qual_role == 'any' or eng_data['role'] == qual_role:
                    if engineer_loads[eng_code] < 8:  # Max 8 new quals per engineer
                        candidates.append((eng_code, engineer_loads[eng_code], eng_data))
            
            if candidates:
                # Assign to engineer with lowest current training load
                candidates.sort(key=lambda x: x[1])
                selected_eng = candidates[0]
                eng_code, current_load, eng_data = selected_eng
                
                # Add to existing assignment or create new one
                existing = next((a for a in optimized_assignments if a['engineer_code'] == eng_code), None)
                if existing:
                    existing['recommended_qualifications'].append(qual)
                    existing['training_effort'] += 1
                    if qual in coverage_gaps['daily_gaps']:
                        existing['daily_impact'] += 1
                else:
                    daily_impact = 1 if qual in coverage_gaps['daily_gaps'] else 0
                    optimized_assignments.append({
                        'engineer_code': eng_code,
                        'engineer_name': eng_data['name'],
                        'role': eng_data['role'],
                        'recommended_qualifications': [qual],
                        'training_effort': 1,
                        'daily_impact': daily_impact,
                        'coverage_improvement': 1
                    })
                
                engineer_loads[eng_code] += 1
        
        print(f"      ✅ Heuristic solution: {len(optimized_assignments)} engineers need training")
        
        return {
            'optimized_assignments': optimized_assignments,
            'total_training_effort': sum(a['training_effort'] for a in optimized_assignments),
            'coverage_improvement': len(coverage_gaps['missing_qualifications']),
            'method': 'Heuristic'
        }
    
    def _get_qualification_role(self, qualification):
        """Determine if qualification is electrical, mechanical, or either"""
        # Look for electrical patterns
        if any(pattern in qualification for pattern in ['DE', 'ME', 'WE']):
            return 'electrical'
        # Look for mechanical patterns  
        elif any(pattern in qualification for pattern in ['DM', 'MM', 'WM', '3MM', 'MMS', 'QM']):
            return 'mechanical'
        else:
            return 'any'  # Could be learned by either role

    def _apply_training_to_current_state(self, training_recommendations):
        """Apply training recommendations to current state to create projected matrices"""
        print("   🔮 Simulating post-training qualification state...")
        
        # Load current state
        current_matrices = self.load_current_qualification_state()
        
        # Apply training recommendations to create projected state
        projected_matrices = {}
        
        for team in [1, 2]:
            if team not in current_matrices or team not in training_recommendations:
                continue
                
            projected_matrices[team] = {}
            team_current = current_matrices[team]
            team_recommendations = training_recommendations[team]
            
            # Create lookup for training assignments
            training_lookup = {}
            for assignment in team_recommendations.get('optimized_assignments', []):
                eng_code = assignment['engineer_code']
                training_lookup[eng_code] = assignment['recommended_qualifications']
            
            # For each engineer in current state, apply training if recommended
            for eng_code, current_profile in team_current.items():
                # Start with current profile
                projected_profile = current_profile.copy()
                projected_profile['qualifications'] = current_profile['qualifications'].copy()
                projected_profile['daily_qualifications'] = current_profile['daily_qualifications'].copy()
                
                # Add training qualifications if engineer has training recommendations
                if eng_code in training_lookup:
                    new_quals = training_lookup[eng_code]
                    
                    # Add new qualifications (avoid duplicates)
                    for qual in new_quals:
                        if qual not in projected_profile['qualifications']:
                            projected_profile['qualifications'].append(qual)
                            
                            # Check if it's a daily qualification
                            if self._is_daily_qualification(qual, team):
                                projected_profile['daily_qualifications'].append(qual)
                    
                    # Recalculate ride assignments from updated qualifications
                    updated_rides = list(set([q.split('.')[0] for q in projected_profile['qualifications']]))
                    projected_profile['assigned_rides'] = updated_rides
                    
                    # Recategorize by ride type
                    projected_profile['type_a_rides'] = [r for r in updated_rides if self._get_ride_type(r) == 'A']
                    projected_profile['type_b_rides'] = [r for r in updated_rides if self._get_ride_type(r) == 'B']
                    projected_profile['type_c_rides'] = [r for r in updated_rides if self._get_ride_type(r) == 'C']
                    
                    # Update coverage score
                    projected_profile['coverage_score'] = len(projected_profile['qualifications'])
                    
                    # Mark as trained
                    projected_profile['training_applied'] = True
                    projected_profile['new_qualifications'] = new_quals
                
                projected_matrices[team][eng_code] = projected_profile
            
            trained_count = len([eng for eng in projected_matrices[team].values() if eng.get('training_applied', False)])
            print(f"      Team {team}: Applied training to {trained_count} engineers")
        
        return projected_matrices


def main():
    """Run training optimization"""
    print("Training Optimization Designer")
    print("Requires PPM data and current qualifications to be loaded first")


if __name__ == "__main__":
    main() 