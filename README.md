# 🎢 Theme Park Maintenance Capacity Optimization System

## Executive Summary

An **AI-powered workforce optimization platform** that ensures **100% preventive maintenance coverage** across theme park operations while **minimizing training costs** and **maximizing operational efficiency**. The system uses advanced mathematical optimization and machine learning to solve complex workforce planning challenges in safety-critical environments.

## 🎯 Business Problem

Theme park maintenance operations face complex workforce optimization challenges:

- **33 rides** requiring **180+ different qualifications** across daily, weekly, and monthly maintenance schedules
- **60 engineers** across 2 teams with varying skill levels and complex shift rotations
- **Critical requirement**: Zero maintenance gaps (safety and operational risk)
- **Challenge**: Optimize training investment for maximum coverage impact while avoiding over-reliance on expert engineers

## 🧠 Technical Solution

### Six Distinct Optimization Algorithms

1. **Qualification Matrix Designer** - Basic qualification distribution
2. **Balanced Coverage Designer** - Workload equalization across teams
3. **Coverage Optimized Designer** - Maximum coverage prioritization
4. **Enhanced Coverage Designer** - Advanced coverage with constraint handling
5. **MILP Optimization Designer** - Industrial-grade mathematical optimization
6. **Training Optimization Designer** - AI-driven progressive skill development ⭐

### Core Technologies

- **Mathematical Linear Programming (MILP)** using PuLP/CBC solver
- **Constraint satisfaction** for complex scheduling requirements
- **Real-time data integration** from HR qualification systems
- **Progressive learning algorithms** that adapt to workforce development
- **Full rotation cycle validation** ensuring 100% coverage guarantee

## 🚀 Key Features

### Real-Time Qualification Analysis
- Processes live HR data (`EngQual.csv`) with 3,900+ active qualifications
- Identifies skill gaps and training opportunities automatically
- Tracks competency development over time

### Intelligent Ride Assignment
- Optimizes engineer-to-ride assignments based on:
  - Current qualifications and experience levels
  - Workload distribution (Team 1: 5 rides avg, Team 2: 6 rides avg)
  - Ride complexity (Type A/B/C classification)
  - Rotation schedule constraints (9-18 week cycles)

### Priority-Based Training Recommendations
- **Smart scoring algorithm**: Daily impact (10pts) + Weekly (5pts) + Monthly (2pts)
- **Focuses training investment** on highest-impact qualifications
- **Prevents over-qualification** - only trains what's needed for assigned rides
- **Progressive optimization** - adapts as engineers develop skills

### Comprehensive Coverage Validation
- Tests all recommendations against **full rotation cycles**
- Validates **36-week coverage scenarios** (multiple rotation cycles)
- Ensures **100% coverage** for daily, weekly, and monthly PPM schedules
- **AM/PM scheduling logic** with preference optimization

## 📊 Business Impact

### Operational Excellence
- **Eliminates maintenance coverage gaps** - zero operational risk
- **100% PPM schedule compliance** across all ride systems
- **Reduced single points of failure** - distributed expertise model
- **Improved response times** - broader qualified engineer availability

### Training ROI Optimization
- **Data-driven training decisions** - no more guesswork
- **Focused skill development** - only necessary qualifications
- **Progressive learning paths** - builds on existing competencies
- **Measurable impact tracking** - quantified training effectiveness

### Workforce Development
- **Clear career progression pathways** for all engineers
- **Reduced expert burnout** - distributed workload
- **Enhanced job satisfaction** - varied work and skill growth
- **Improved retention** - investment in employee development

### Financial Benefits
- **Optimized labor costs** - efficient workload distribution
- **Reduced overtime expenses** - better coverage planning
- **Lower training waste** - targeted skill development
- **Predictable maintenance costs** - reliable coverage model

## 🏗️ System Architecture

```
capacity/
├── src/analysis/           # Core optimization algorithms
│   ├── milp_optimization_designer.py      # Mathematical optimization
│   ├── training_optimization_designer.py  # AI training recommendations
│   ├── coverage_validator.py             # Validation framework
│   └── ...                              # Other optimization approaches
├── data/
│   ├── raw/EngQual.csv                  # Live qualification data
│   ├── processed/                       # Processed engineer/ride data
│   └── ...
├── outputs/                             # Results and reports
│   ├── current/                         # Latest optimization results
│   └── qualification_optimization/      # Historical optimization data
├── scripts/                             # Automation and utilities
└── config/                             # System configuration
```

## 🎮 Usage

### Option 6: Training Optimization (Recommended)

```bash
python3 run_optimization.py
# Select option 6 for AI-driven training optimization
```

### Outputs Generated

1. **CSV Files for Management Review**:
   - `training_summary_by_engineer.csv` - Priority scores and training effort
   - `training_breakdown_by_ride.csv` - Ride-by-ride qualification analysis
   - `specific_qualifications_needed.csv` - Exact training requirements
   - `training_priority_ranking.csv` - Overall priority ranking

2. **JSON Files for System Integration**:
   - `training_recommendations.json` - Detailed training plans
   - `current_qualification_state.json` - Current team competency
   - `detailed_training_report.json` - Comprehensive analysis

3. **Validation Reports**:
   - Coverage validation across full rotation cycles
   - Risk assessment and operational impact analysis

### Weekly Workflow

1. **Update qualification data**: Replace `data/raw/EngQual.csv` with latest HR export
2. **Run optimization**: Execute Option 6 training optimization
3. **Review recommendations**: Open CSV files in Excel/Google Sheets
4. **Implement training**: Focus on highest priority engineers
5. **Monitor progress**: Track qualification development over time

## 🎯 Strategic Implementation: Training Optimization Approach

### The Philosophy Shift

Moving from **expert-dependent operations** to **distributed competency model**:

**Current State Problems**:
- Over-reliance on senior engineers (single points of failure)
- Limited career progression for junior staff
- Burnout risk for expert engineers
- Operational vulnerability during absences

**Target State Benefits**:
- Resilient operations with redundant expertise
- Clear advancement pathways for all engineers
- Sustainable workload distribution
- Reduced operational risk profile

### Natural Progressive Optimization Strategy

The system is designed to **trust the mathematical optimization** and achieve balance through **progressive rebalancing** rather than artificial constraints:

#### **Why This Approach Works**

**Priority Algorithm Naturally Focuses on High Impact**:
```
Priority Score = (Daily Impact × 10) + (Weekly Impact × 5) + (Monthly Impact × 2)
```

- **Low-qualified engineers** with **0 daily qualifications** get highest priority scores
- **Over-qualified engineers** with **many daily qualifications** naturally get lower priority
- **System automatically targets** maximum operational impact areas

**Current Priority Examples**:
- John Booth (3 quals): Score 104 → **20 training recommendations**
- Rob Parker (72 quals): Score 26 → **11 training recommendations**

#### **Progressive Rebalancing Effect**

**Phase 1** (Months 1-6): **Focus on Critical Gaps**
- Train engineers with **0-10 qualifications** to basic competency
- **Massive capacity increase** from bringing low-qualified engineers to viable levels
- **Daily PPM coverage** dramatically improves

**Phase 2** (Months 6-12): **Natural Workload Redistribution**
- **MILP recalculates** assignments based on improved competency
- **Over-qualified engineers** see **reduced assignment burden** automatically
- **Training recommendations shift** to next-lowest qualified engineers

**Phase 3** (Months 12+): **Equilibrium and Specialization**
- **Balanced competency** across all critical systems
- **Expert engineers** transition to **specialist/mentor roles**
- **Training focus** shifts to skill maintenance and strategic gaps

#### **Strategic Advantages of Natural Progression**

✅ **Maximum ROI**: Biggest impact from training low-competency engineers first  
✅ **Trust the Math**: MILP finds optimal balance without artificial constraints  
✅ **Organic Evolution**: System adapts to changing competency landscape  
✅ **Change Management**: Start with obvious gaps, build confidence gradually  
✅ **Future-Proof**: No over-engineering based on current assumptions  

#### **Implementation Philosophy**

**Don't Over-Constrain Early**: Avoid adding compensation tier constraints initially
- Let the system discover natural competency distribution
- Focus on high-impact training (daily PPMs for low-qualified engineers)
- Allow mathematical optimization to find optimal workforce balance

**Progressive Assessment**: Re-evaluate system recommendations as competency develops
- 6-month review to observe natural rebalancing effects
- 12-month assessment of overall competency distribution
- Strategic adjustments only if specific gaps emerge

### Implementation Timeline

#### Short-Term (3-6 months)
**Challenges**:
- Increased training resource requirements
- Temporary skill gaps during development
- Quality control during learning phase
- Change management resistance

**Early Wins**:
- Visible competency development progress
- Reduced single-engineer dependencies
- Improved team morale and engagement
- Data-driven training decisions

#### Long-Term (12+ months)
**Operational Benefits**:
- Redundant expertise across all critical systems
- Flexible scheduling with broader qualified pool
- Reduced overtime and emergency callout costs
- Enhanced maintenance quality through diverse perspectives

**Strategic Advantages**:
- Scalable operations model
- Predictable training and development costs
- Improved succession planning
- Enhanced organizational resilience

### Risk Management

1. **Gradual Transition**: Phased skill transfer with expert oversight
2. **Safety Protocols**: Clear escalation paths during learning phases
3. **Quality Assurance**: Paired learning and competency validation
4. **Contingency Planning**: Emergency coverage procedures

## 🔧 Installation & Setup

### Prerequisites
```bash
# Python 3.9+
pip install -r requirements.txt
```

### Required Dependencies
- `pulp` - Mathematical optimization
- `pandas` - Data processing
- `numpy` - Numerical computing
- `json` - Data serialization

### Configuration
1. Update `config/config.yaml` with your specific ride and team configurations
2. Ensure `data/raw/EngQual.csv` contains current qualification data
3. Verify team rotas in `data/processed/parsed_rotas/`

### Validation
```bash
python3 validate_qualifications.py
```

## 📈 Performance Metrics

### System Performance
- **Coverage Achievement**: 100% across all PPM schedules
- **Optimization Speed**: < 2 minutes for full team analysis
- **Scalability**: Handles 60+ engineers, 33 rides, 180+ qualifications
- **Accuracy**: Deterministic results for identical input data

### Business Metrics
- **Training Efficiency**: Focused on 27-29 engineers needing development
- **Qualification Distribution**: Team 1 (367 quals), Team 2 (522 quals)
- **Priority Focus**: Top 10 engineers account for 60% of training impact
- **Cost Optimization**: Eliminates unnecessary over-qualification

## 🤝 Contributing

This system is designed for theme park maintenance operations but can be adapted for:
- Manufacturing maintenance scheduling
- Healthcare staff optimization
- Technical support team planning
- Any qualification-based workforce optimization

## 📞 Support

For technical questions or implementation support, refer to:
- System logs in `outputs/current/`
- Validation reports for troubleshooting
- CSV exports for detailed analysis

## 🏆 Success Metrics

**Operational Excellence**:
- Zero maintenance coverage gaps
- 100% PPM schedule compliance
- Reduced emergency maintenance incidents

**Workforce Development**:
- Measurable skill progression across all engineers
- Improved job satisfaction and retention rates
- Clear career advancement opportunities

**Financial Performance**:
- Optimized training investment ROI
- Reduced overtime and emergency costs
- Predictable maintenance operations budget

---

*Built with mathematical optimization and AI-driven workforce planning for safety-critical theme park operations.*