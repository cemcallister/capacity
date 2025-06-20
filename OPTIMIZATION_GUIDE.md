# Qualification Optimization System - Quick Start Guide

## 🚀 How to Run the System

### **Option 1: Generate New Optimized Qualification Matrices**
```bash
python3 run_optimization.py
```

**What this does:**
- Loads all PPM and engineer data
- Creates qualification matrices optimized for operational coverage
- Validates results against real shift patterns
- Exports results to `outputs/coverage_optimized_qualification/`

**Output files:**
- `coverage_optimized_team_1_qualification_matrix.json`
- `coverage_optimized_team_2_qualification_matrix.json`
- `coverage_optimized_validation.json`
- `coverage_optimized_summary.md`

---

### **Option 2: Validate Existing Qualification Matrices**
```bash
python3 validate_qualifications.py
```

**What this does:**
- Tests existing qualification matrices against operational requirements
- Shows coverage percentages for daily, weekly, monthly PPMs
- Identifies coverage gaps and risk levels
- Can compare original vs improved approaches

**When to use:**
- Test qualification assignments from any source
- Compare different optimization approaches
- Verify operational feasibility

---

## 📊 Understanding the Results

### **Coverage Percentages:**
- **Daily PPMs**: Must be 100% (critical - needed every day)
- **Weekly PPMs**: Should be 90%+ (important for maintenance schedules)
- **Monthly PPMs**: Can be 80%+ (flexible scheduling)

### **Status Levels:**
- **✅ EXCELLENT**: >95% coverage across all PPM types
- **🟡 GOOD**: >90% coverage across all PPM types
- **🟠 ACCEPTABLE**: 80-90% coverage (some gaps but manageable)
- **❌ INSUFFICIENT**: <80% coverage (significant operational issues)

### **Risk Levels:**
- **LOW**: Good redundancy, multiple engineers per qualification
- **MEDIUM**: Some single points of failure
- **HIGH**: Many critical qualifications with only 1 engineer
- **CRITICAL**: >50% of qualifications are single points of failure

---

## 🔧 Key Improvements in the System

### **What's Fixed:**
1. **Multiple Engineer Logic**: Accounts for PPMs requiring >3 hours (need multiple engineers)
2. **Shift Pattern Validation**: Tests against real rota data
3. **Proper Redundancy**: Ensures 2+ engineers per ride for coverage
4. **Role-Specific Assignments**: Electrical engineers get electrical PPMs only

### **Why This Matters:**
- **SMLR daily mechanical**: 3.34 hours total → needs 2 engineers working together
- **Original approach**: Assigned 1 engineer per ride → failed when that engineer unavailable
- **Improved approach**: Multiple engineers per ride → better coverage even with shift patterns

---

## 📁 File Structure

```
outputs/
├── qualification_optimization/          # Original approach results
│   ├── team_1_qualification_matrix.json
│   └── team_2_qualification_matrix.json
└── coverage_optimized_qualification/    # Improved approach results
    ├── coverage_optimized_team_1_qualification_matrix.json
    ├── coverage_optimized_team_2_qualification_matrix.json
    ├── coverage_optimized_validation.json
    └── coverage_optimized_summary.md
```

---

## 🎯 Next Steps for Further Improvement

1. **Increase redundancy** for daily PPMs showing 0% coverage
2. **Analyze specific coverage gaps** in validation results
3. **Consider cross-training** between electrical and mechanical roles
4. **Implement iterative optimization** using validation feedback

---

## 💡 Pro Tips

- Run `validate_qualifications.py` with "both" to compare approaches
- Check the `.md` summary files for human-readable results
- Focus on improving daily PPM coverage first (most critical)
- Use validation results to identify which qualifications need more engineers 