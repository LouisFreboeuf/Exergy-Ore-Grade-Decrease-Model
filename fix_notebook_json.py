#!/usr/bin/env python3
"""
Script to fix the JSON error in the SurplusEx.ipynb notebook.
The issue is with f-strings using double quotes inside the notebook JSON.
"""

import json
import re
from pathlib import Path

def fix_notebook_json(notebook_path):
    """Fix JSON issues in Jupyter notebook caused by f-strings with double quotes."""
    
    print(f"Fixing JSON issues in {notebook_path}")
    
    # Read the notebook file
    with open(notebook_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and fix problematic f-strings with double quotes
    # Pattern: f"...{...}..." where the inner part might contain quotes
    # We'll convert these to single quotes: f'...{...}...'
    
    # Specific patterns to fix:
    # 1. f"Applied to {number of elements} elements"
    # 2. f"{number of elements} elements"
    
    patterns_to_fix = [
        (r'f"Applied to \{number of elements\} elements"', r"f'Applied to {number of elements} elements'"),
        (r'f"\{number of elements\} elements"', r"f'{number of elements} elements'"),
        (r'f"Applied to \{len\(OGD_df\)\} elements"', r"f'Applied to {len(OGD_df)} elements'"),
        (r'f"\{len\(OGD_df\)\} elements"', r"f'{len(OGD_df)} elements'"),
    ]
    
    original_content = content
    for pattern, replacement in patterns_to_fix:
        content = re.sub(pattern, replacement, content)
    
    if content != original_content:
        print("Fixed f-string quotes in notebook")
        # Write the fixed content back
        with open(notebook_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Notebook saved with fixes")
    else:
        print("No f-string issues found to fix")
    
    # Also check for any remaining f"..." patterns that might cause issues
    f_string_patterns = re.findall(r'f"[^"]*"', content)
    if f_string_patterns:
        print(f"Found {len(f_string_patterns)} f-strings with double quotes:")
        for i, pattern in enumerate(f_string_patterns[:5]):  # Show first 5
            print(f"  {i+1}. {pattern}")
    
    return content

def main():
    notebook_path = Path("SurplusEx.ipynb")
    
    if not notebook_path.exists():
        print(f"Notebook {notebook_path} not found!")
        return
    
    # Fix the notebook
    fix_notebook_json(notebook_path)
    
    print("Notebook JSON fix completed.")

if __name__ == "__main__":
    main()