#!/usr/bin/env python3

"""
Script to execute SurplusEx.ipynb for all 8 configurations defined in the workflow.
Uses local Python environment with Brightway.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

# Define the configurations
configs = [
    {
        "name": "all_vieira_natural_resources",
        "viera_csv_input_data": "inputs/sop-vieira-constants_all.csv",
        "input_for_xi": "inputs/sop-vieira-constants_all.csv",
        "focus": "natural_resource"
    },
    {
        "name": "all_vieira_dissipation",
        "viera_csv_input_data": "inputs/sop-vieira-constants_all.csv",
        "input_for_xi": "inputs/sop-vieira-constants_all.csv",
        "focus": "dissipation"
    },
    {
        "name": "all_valero_natural",
        "viera_csv_input_data": "inputs/sop-vieira-constants_all.csv",
        "input_for_xi": "inputs/valero-constants_with_xm.csv",
        "focus": "natural_resource"
    },
    {
        "name": "all_valero_dissipation",
        "viera_csv_input_data": "inputs/sop-vieira-constants_all.csv",
        "input_for_xi": "inputs/valero-constants_with_xm.csv",
        "focus": "dissipation"
    },
    {
        "name": "updatedFe_vieira_natural_resources",
        "viera_csv_input_data": "inputs/sop-vieira-constants_updatedFe.csv",
        "input_for_xi": "inputs/sop-vieira-constants_updatedFe.csv",
        "focus": "natural_resource"
    },
    {
        "name": "updatedFe_vieira_dissipation",
        "viera_csv_input_data": "inputs/sop-vieira-constants_updatedFe.csv",
        "input_for_xi": "inputs/sop-vieira-constants_updatedFe.csv",
        "focus": "dissipation"
    },
    {
        "name": "updatedFe_valero_natural",
        "viera_csv_input_data": "inputs/sop-vieira-constants_updatedFe.csv",
        "input_for_xi": "inputs/valero-constants_with_xm.csv",
        "focus": "natural_resource"
    },
    {
        "name": "updatedFe_valero_dissipation",
        "viera_csv_input_data": "inputs/sop-vieira-constants_updatedFe.csv",
        "input_for_xi": "inputs/valero-constants_with_xm.csv",
        "focus": "dissipation"
    }
]

def modify_notebook(original_path, output_path, params):
    """Modify a Jupyter notebook to inject parameters."""
    with open(original_path, 'r') as f:
        nb = json.load(f)
    
    # Update parameter values in the notebook cells
    for cell in nb['cells']:
        if cell.get('cell_type') == 'code':
            source = ''.join(cell['source'])
            
            # Update viera_csv_input_data
            if 'viera_csv_input_data = "inputs/sop-vieira-constants_all.csv"' in source:
                cell['source'] = [
                    source.replace(
                        'viera_csv_input_data = "inputs/sop-vieira-constants_all.csv"',
                        f'viera_csv_input_data = "{params["viera_csv_input_data"]}"'
                    )
                ]
            
            # Update input_for_xi
            if 'input_for_xi = valero_csv_input_data' in source:
                cell['source'] = [
                    source.replace(
                        'input_for_xi = valero_csv_input_data',
                        f'input_for_xi = "{params["input_for_xi"]}"'
                    )
                ]
            
            # Update focus
            if 'focus = "natural_resources"' in source:
                cell['source'] = [
                    source.replace(
                        'focus = "natural_resources"',
                        f'focus = "{params["focus"]}"'
                    )
                ]
    
    # Write the modified notebook
    with open(output_path, 'w') as f:
        json.dump(nb, f, indent=1)

def execute_notebook(notebook_path, output_path, timeout=1800):
    """Execute a Jupyter notebook and save the output."""
    cmd = [
        'jupyter', 'nbconvert',
        '--to', 'notebook',
        '--execute', notebook_path,
        '--output', output_path,
        '--ExecutePreprocessor.timeout=' + str(timeout),
        '--ExecutePreprocessor.allow_errors=False'
    ]
    
    print(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 60)
    
    if result.returncode != 0:
        print(f"Error executing notebook:")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        return False
    
    return True

def main():
    # Get the script directory
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    
    # Create results directory if it doesn't exist
    results_dir = script_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    print("Starting SurplusEx.ipynb execution for all configurations...")
    print(f"Results will be saved in the {results_dir} directory.")
    print()
    
    # Loop through all configurations
    for config in configs:
        print("=" * 50)
        print(f"Processing configuration: {config['name']}")
        print(f"  viera_csv_input_data: {config['viera_csv_input_data']}")
        print(f"  input_for_xi: {config['input_for_xi']}")
        print(f"  focus: {config['focus']}")
        print("=" * 50)
        
        # Create a temporary copy of the notebook with the parameters injected
        temp_notebook = script_dir / f"temp_SurplusEx_{config['name']}.ipynb"
        output_notebook = results_dir / f"SurplusEx_{config['name']}.ipynb"
        
        # Copy and modify the notebook
        print("Preparing notebook with parameters...")
        try:
            modify_notebook("SurplusEx.ipynb", str(temp_notebook), config)
        except Exception as e:
            print(f"Error modifying notebook: {e}")
            continue
        
        # Execute the notebook
        print("Executing notebook...")
        try:
            success = execute_notebook(
                str(temp_notebook),
                str(output_notebook),
                timeout=1800
            )
            
            if not success:
                print(f"Error: Notebook execution failed for {config['name']}")
                continue
            
            print(f"Notebook executed successfully for {config['name']}")
            
            # Move all_results.json to results directory with config suffix
            all_results_path = script_dir / "all_results.json"
            if all_results_path.exists():
                target_path = results_dir / f"all_results_{config['name']}.json"
                all_results_path.rename(target_path)
                print(f"Moved all_results.json to {target_path}")
            else:
                print("Warning: all_results.json not found after execution")
            
        except subprocess.TimeoutExpired:
            print(f"Timeout: Notebook execution timed out for {config['name']}")
        except Exception as e:
            print(f"Error executing notebook: {e}")
        finally:
            # Clean up temporary notebook
            if temp_notebook.exists():
                temp_notebook.unlink()
        
        print()
    
    print("All configurations processed!")
    print("Results saved in results/ directory.")

if __name__ == "__main__":
    main()