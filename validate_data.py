#!/usr/bin/env python3
"""
Data validation script for Exergy Ore Grade Decrease Model.
Checks CSV files for basic integrity issues.
"""

import csv
import os
import sys
from pathlib import Path


def validate_csv(filepath):
    """Validate a CSV file for basic issues."""
    issues = []
    
    if not os.path.exists(filepath):
        issues.append(f"File not found: {filepath}")
        return issues
    
    try:
        with open(filepath, 'r', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
            if len(rows) == 0:
                issues.append(f"Empty file: {filepath}")
            
            # Check for consistent column count
            if len(rows) > 0:
                col_count = len(rows[0])
                for i, row in enumerate(rows[1:], start=2):
                    if len(row) != col_count:
                        issues.append(f"Inconsistent columns at row {i}: expected {col_count}, got {len(row)}")
                        # Only report first 5 issues
                        if len(issues) >= 5:
                            break
                            
    except Exception as e:
        issues.append(f"Error reading {filepath}: {str(e)}")
    
    return issues


def main():
    """Run validation on all CSV files."""
    data_dir = Path(__file__).parent / "data"
    csv_files = list(data_dir.glob("*.csv"))
    
    print(f"Validating {len(csv_files)} CSV files in {data_dir}...")
    
    all_issues = []
    for csv_file in sorted(csv_files):
        issues = validate_csv(csv_file)
        if issues:
            all_issues.extend(issues)
            print(f"  ❌ {csv_file.name}: {len(issues)} issue(s)")
        else:
            print(f"  ✓ {csv_file.name}")
    
    if all_issues:
        print(f"\n{len(all_issues)} issue(s) found:")
        for issue in all_issues:
            print(f"  - {issue}")
        sys.exit(1)
    else:
        print("\n✓ All CSV files are valid!")
        sys.exit(0)


if __name__ == "__main__":
    main()
