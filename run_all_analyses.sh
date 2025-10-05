#!/bin/bash

# EACL Statistical Enhancement Pipeline
# =====================================
# Runs all NO-API statistical analyses for paper improvement.
# Execute in tmux session for long-running stability.

set -e  # Exit on error

echo "========================================================================"
echo "EACL PAPER STATISTICAL ENHANCEMENT PIPELINE"
echo "========================================================================"
echo ""
echo "Starting time: $(date)"
echo ""

# 1. Statistical corrections (multiple comparison, effect sizes, power)
echo "========================================================================"
echo "1. Running statistical enhancements..."
echo "========================================================================"
python3 statistical_enhancements.py
echo ""
echo "✓ Completed: statistical_enhancements.py"
echo ""

# 2. Language family and script analysis
echo "========================================================================"
echo "2. Running language family & script analysis..."
echo "========================================================================"
python3 language_family_analysis.py
echo ""
echo "✓ Completed: language_family_analysis.py"
echo ""

# 3. Forest plots
echo "========================================================================"
echo "3. Generating forest plots..."
echo "========================================================================"
python3 generate_forest_plot.py
echo ""
echo "✓ Completed: generate_forest_plot.py"
echo ""

# Summary
echo "========================================================================"
echo "PIPELINE COMPLETE"
echo "========================================================================"
echo ""
echo "End time: $(date)"
echo ""
echo "Generated CSV files:"
ls -lh *.csv | grep -E "(statistical|family|script|language|template)" || echo "  (none found - check errors above)"
echo ""
echo "Generated plot files:"
ls -lh forest_plot_* 2>/dev/null || echo "  (none found - check errors above)"
echo ""
echo "All analyses complete. Review outputs before updating paper."
echo ""
