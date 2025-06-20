"""
PPM Capacity Optimization Analysis
==================================

This module analyzes theme park maintenance capacity planning to determine
optimal qualification portfolios for each team to ensure full PPM coverage.

Key Constraints:
- Daily PPMs: Must be done every day in 3hr AM window
- Weekly PPMs: Must be completed Mon-Fri (3hr AM or PM window)
- Monthly PPMs: Must be completed Mon-Fri (3hr AM or PM window)
- Each engineer needs specific qualifications for specific PPMs
- Each engineer should be assigned at least 2 Type A rides
- Team rotas are fixed and cannot be changed
"""

import json
import pandas as pd
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import numpy as np


class PPMCapacityOptimizer:
    """Optimize PPM qualification assignments for maintenance teams"""
    
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.rides_info = {}
        self.ppms_by_type = {'daily': {}, 'weekly': {}, 'monthly': {}}
        self.engineer_quals = {}
        self.team_rotas = {}
        self.shift_definitions = {}
        
        # Load all data
        self._load_data()
    
    def _load_data(self):
        """Load all required data files"""
        print("🔄 Loading data...")
        
        # Load ride information
        with open(self.data_dir / "processed/ride_info.json") as f:
            data = json.load(f)
            self.rides_info = data["rides"]
        
        # Load shift definitions
        with open(self.data_dir / "processed/shift_definitions.json") as f:
            self.shift_definitions = json.load(f)
        
        # Load PPM data for each type
        for ppm_type in ['daily', 'weekly', 'monthly']:
            ppm_dir = self.data_dir / f"raw/ppms/{ppm_type}"
            for ppm_file in ppm_dir.glob("*.json"):
                ride_id = ppm_file.stem
                with open(ppm_file) as f:
                    self.ppms_by_type[ppm_type][ride_id] = json.load(f)
        
        # Load engineer qualifications
        eng_qual_df = pd.read_csv(self.data_dir / "raw/EngQual.csv")
        self.engineer_quals = self._process_engineer_qualifications(eng_qual_df)
        
        # Load team rotas
        for team in [1, 2]:
            for role in ['mech', 'elec']:
                rota_file = self.data_dir / f"processed/parsed_rotas/parsed_team{team}_{role}_rota.json"
                if rota_file.exists():
                    with open(rota_file) as f:
                        key = f"team_{team}_{role}"
                        self.team_rotas[key] = json.load(f)
        
        print("✅ Data loaded successfully")
    
    def _process_engineer_qualifications(self, df):
        """Process engineer qualifications from CSV"""
        quals = defaultdict(list)
        for _, row in df.iterrows():
            if pd.notna(row['Employee Code']) and pd.notna(row['Qualification']):
                quals[row['Employee Code']].append(row['Qualification'])
        return dict(quals)
    
    def analyze_team_composition(self):
        """Analyze ride distribution by team and type"""
        print("\n📊 TEAM COMPOSITION ANALYSIS")
        print("=" * 50)
        
        team_data = defaultdict(lambda: {'A': [], 'B': [], 'C': [], 'total': 0})
        
        for ride_id, info in self.rides_info.items():
            team = info['team_responsible']
            ride_type = info['type']
            team_data[team][ride_type].append(ride_id)
            team_data[team]['total'] += 1
        
        for team in sorted(team_data.keys()):
            data = team_data[team]
            print(f"\n🏢 TEAM {team}:")
            print(f"   Type A (Complex):    {len(data['A'])} rides - {data['A']}")
            print(f"   Type B (Medium):     {len(data['B'])} rides - {data['B']}")
            print(f"   Type C (Simple):     {len(data['C'])} rides - {data['C']}")
            print(f"   TOTAL:               {data['total']} rides")
            
            # Check Type A constraint
            type_a_count = len(data['A'])
            print(f"   Type A constraint:   Each engineer needs ≥2 Type A rides")
            print(f"                        Available: {type_a_count} Type A rides")
        
        return team_data
    
    def analyze_ppm_workload(self):
        """Analyze PPM workload by team and type"""
        print("\n⚙️  PPM WORKLOAD ANALYSIS")
        print("=" * 50)
        
        workload = defaultdict(lambda: {
            'daily': {'total_hours': 0, 'electrical': 0, 'mechanical': 0, 'ppms': []},
            'weekly': {'total_hours': 0, 'electrical': 0, 'mechanical': 0, 'ppms': []},
            'monthly': {'total_hours': 0, 'electrical': 0, 'mechanical': 0, 'ppms': []}
        })
        
        # Calculate workload for each team
        for ppm_type in ['daily', 'weekly', 'monthly']:
            for ride_id, ppm_data in self.ppms_by_type[ppm_type].items():
                if ride_id in self.rides_info:
                    team = self.rides_info[ride_id]['team_responsible']
                    ride_type = self.rides_info[ride_id]['type']
                    
                    for ppm in ppm_data['ppms']:
                        duration = ppm['duration_hours']
                        maintenance_type = ppm['maintenance_type'].lower()
                        
                        workload[team][ppm_type]['total_hours'] += duration
                        workload[team][ppm_type][maintenance_type] += duration
                        workload[team][ppm_type]['ppms'].append({
                            'ride_id': ride_id,
                            'ride_type': ride_type,
                            'ppm_code': ppm['ppm_code'],
                            'qualification': ppm['qualification_code'],
                            'duration': duration,
                            'maintenance_type': maintenance_type
                        })
        
        # Display workload analysis
        for team in sorted(workload.keys()):
            print(f"\n🏢 TEAM {team} WORKLOAD:")
            
            for ppm_type in ['daily', 'weekly', 'monthly']:
                data = workload[team][ppm_type]
                total_ppms = len(data['ppms'])
                
                print(f"\n   📅 {ppm_type.upper()} PPMs:")
                print(f"      Total PPMs:        {total_ppms}")
                print(f"      Total Hours:       {data['total_hours']:.2f}")
                print(f"      Electrical Hours:  {data['electrical']:.2f}")
                print(f"      Mechanical Hours:  {data['mechanical']:.2f}")
                
                if ppm_type == 'daily':
                    print(f"      Daily Constraint:  Must complete {data['total_hours']:.2f}hrs in 3hr AM window")
                    if data['total_hours'] > 3:
                        needed_engineers = np.ceil(data['total_hours'] / 3)
                        print(f"      ⚠️  REQUIRES:       {needed_engineers:.0f} engineers minimum")
        
        return workload
    
    def analyze_qualification_requirements(self):
        """Analyze required qualifications by team"""
        print("\n🎓 QUALIFICATION REQUIREMENTS")
        print("=" * 50)
        
        team_quals = defaultdict(lambda: {
            'daily': set(), 'weekly': set(), 'monthly': set(), 'all': set()
        })
        
        # Collect all required qualifications by team
        for ppm_type in ['daily', 'weekly', 'monthly']:
            for ride_id, ppm_data in self.ppms_by_type[ppm_type].items():
                if ride_id in self.rides_info:
                    team = self.rides_info[ride_id]['team_responsible']
                    
                    for ppm in ppm_data['ppms']:
                        qual = ppm['qualification_code']
                        team_quals[team][ppm_type].add(qual)
                        team_quals[team]['all'].add(qual)
        
        # Display qualification requirements
        for team in sorted(team_quals.keys()):
            quals = team_quals[team]
            print(f"\n🏢 TEAM {team} QUALIFICATION REQUIREMENTS:")
            print(f"   Daily PPMs:    {len(quals['daily'])} unique qualifications")
            print(f"   Weekly PPMs:   {len(quals['weekly'])} unique qualifications")
            print(f"   Monthly PPMs:  {len(quals['monthly'])} unique qualifications")
            print(f"   TOTAL UNIQUE:  {len(quals['all'])} qualifications needed")
            
            print(f"\n   📋 All Required Qualifications:")
            for i, qual in enumerate(sorted(quals['all']), 1):
                print(f"      {i:2d}. {qual}")
        
        return team_quals
    
    def analyze_rota_capacity(self):
        """Analyze available capacity based on current rotas"""
        print("\n📅 ROTA CAPACITY ANALYSIS")
        print("=" * 50)
        
        capacity = defaultdict(dict)
        
        for rota_key, rota_data in self.team_rotas.items():
            team_num = rota_key.split('_')[1]
            role = rota_key.split('_')[2]
            
            print(f"\n🏢 TEAM {team_num} - {role.upper()} ENGINEERS:")
            
            # Count available engineers per day
            daily_capacity = defaultdict(list)
            
            # Sample first week to understand pattern
            if rota_data:
                first_week = list(rota_data.keys())[0]
                week_data = rota_data[first_week]
                
                days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                
                for day_idx, day in enumerate(days):
                    early_engineers = []
                    late_engineers = []
                    
                    for engineer, shifts in week_data.items():
                        if day_idx < len(shifts):
                            shift = shifts[day_idx]
                            if shift == 'E':  # Early shift
                                early_engineers.append(engineer)
                            elif shift == 'L':  # Late shift
                                late_engineers.append(engineer)
                    
                    daily_capacity[day] = {
                        'early': early_engineers,
                        'late': late_engineers,
                        'early_count': len(early_engineers),
                        'late_count': len(late_engineers)
                    }
                
                # Display capacity
                total_engineers = len(week_data)
                print(f"   Total Engineers:   {total_engineers}")
                
                for day in days:
                    cap = daily_capacity[day]
                    print(f"   {day:9}: Early={cap['early_count']:2d}, Late={cap['late_count']:2d}")
                
                # PPM window analysis
                print(f"\n   💡 PPM CAPACITY:")
                weekday_early_avg = np.mean([daily_capacity[day]['early_count'] 
                                           for day in days[:5]])  # Mon-Fri
                weekday_late_avg = np.mean([daily_capacity[day]['late_count'] 
                                          for day in days[:5]])
                
                print(f"   AM PPM Window (Mon-Fri avg):  {weekday_early_avg:.1f} engineers")
                print(f"   PM PPM Window (Mon-Fri avg):  {weekday_late_avg:.1f} engineers")
                print(f"   Daily PPM Capacity:           {weekday_early_avg * 3:.1f} hours/day")
                print(f"   Weekly PPM Capacity:          {(weekday_early_avg + weekday_late_avg) * 3 * 5:.1f} hours/week")
            
            capacity[f"team_{team_num}"][role] = daily_capacity
        
        return capacity
    
    def find_optimal_qualifications(self):
        """Find optimal qualification assignment for each team"""
        print("\n🎯 OPTIMIZATION ANALYSIS")
        print("=" * 50)
        
        # Get all required data
        team_composition = self.analyze_team_composition()
        workload = self.analyze_ppm_workload()
        qual_requirements = self.analyze_qualification_requirements()
        capacity = self.analyze_rota_capacity()
        
        print(f"\n📋 OPTIMIZATION SUMMARY:")
        
        for team in [1, 2]:
            print(f"\n🏢 TEAM {team} RECOMMENDATIONS:")
            
            # Check capacity vs workload
            team_workload = workload[team]
            daily_hours = team_workload['daily']['total_hours']
            
            print(f"   📊 Workload Analysis:")
            print(f"      Daily PPM Hours:     {daily_hours:.2f} (limit: 3.0)")
            print(f"      Weekly PPM Hours:    {team_workload['weekly']['total_hours']:.2f}")
            print(f"      Monthly PPM Hours:   {team_workload['monthly']['total_hours']:.2f}")
            
            if daily_hours > 3:
                min_engineers = np.ceil(daily_hours / 3)
                print(f"      ⚠️  CRITICAL: Need minimum {min_engineers:.0f} engineers for daily PPMs")
            
            # Type A qualification constraint (each engineer qualified on ≥2 Type A rides)
            type_a_rides = len(team_composition[team]['A'])
            
            # Calculate required engineers based on daily PPM workload
            min_engineers_daily = max(np.ceil(daily_hours / 3), 1)
            
            print(f"\n   🎯 Engineer Constraints:")
            print(f"      Type A Rides:        {type_a_rides}")
            print(f"      Min Engineers (daily): {min_engineers_daily:.0f} (workload constraint)")
            print(f"      Required Quals:      {len(qual_requirements[team]['all'])}")
            print(f"      Type A Constraint:   Each engineer qualified on ≥2 Type A rides")
            
            # Check if Type A constraint is feasible
            type_a_feasible = type_a_rides >= 2  # Need at least 2 Type A rides for constraint
            
            print(f"\n   💡 RECOMMENDATIONS:")
            if not type_a_feasible:
                print(f"      ⚠️  Type A constraint impossible: Only {type_a_rides} Type A rides available")
                print(f"      🔧 SOLUTION: Reduce to 1 Type A ride per engineer")
                optimal_engineers = min_engineers_daily
            else:
                optimal_engineers = min_engineers_daily
                print(f"      ✅ Type A constraint: FEASIBLE")
            
            # Calculate qualification distribution
            total_quals = len(qual_requirements[team]['all'])
            quals_per_engineer = np.ceil(total_quals / optimal_engineers)
            
            # Type A qualifications per engineer
            type_a_quals_needed = optimal_engineers * 2  # Each needs 2 Type A rides
            type_a_coverage = "POSSIBLE" if type_a_quals_needed <= type_a_rides * 10 else "TIGHT"  # Assume ~10 quals per ride
            
            print(f"      ✅ Optimal Engineers: {optimal_engineers:.0f}")
            print(f"      📚 Total Quals Needed: {total_quals}")
            print(f"      📚 Quals per Engineer: {quals_per_engineer:.0f}")
            print(f"      ⏱️  PPM Hours per Engineer: {daily_hours / optimal_engineers:.2f}/day")
            print(f"      🎯 Type A Quals/Engineer: 2 (constraint)")
            print(f"      �� Type A Coverage: {type_a_coverage}")
        
        return {
            'team_composition': team_composition,
            'workload': workload, 
            'qualifications': qual_requirements,
            'capacity': capacity
        }
    
    def generate_report(self):
        """Generate comprehensive optimization report"""
        print("\n" + "="*80)
        print("🎢 THEME PARK MAINTENANCE CAPACITY OPTIMIZATION REPORT")
        print("="*80)
        
        results = self.find_optimal_qualifications()
        
        print(f"\n📈 EXECUTIVE SUMMARY:")
        print(f"   • Analysis covers {len(self.rides_info)} rides across 2 teams")
        print(f"   • {sum(len(ppms) for ppms in self.ppms_by_type['daily'].values())} daily PPMs")
        print(f"   • {sum(len(ppms) for ppms in self.ppms_by_type['weekly'].values())} weekly PPMs")  
        print(f"   • {sum(len(ppms) for ppms in self.ppms_by_type['monthly'].values())} monthly PPMs")
        print(f"   • Fixed rota pattern constrains available capacity")
        print(f"   • Each engineer must cover ≥2 Type A rides")
        
        return results


def main():
    """Run the complete PPM capacity optimization analysis"""
    optimizer = PPMCapacityOptimizer()
    results = optimizer.generate_report()
    
    print(f"\n✅ Analysis complete! Results saved in memory.")
    print(f"💡 Next steps: Use results to design qualification matrix")
    
    return optimizer, results


if __name__ == "__main__":
    optimizer, results = main() 