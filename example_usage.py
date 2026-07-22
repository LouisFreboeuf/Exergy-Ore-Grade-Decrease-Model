#!/usr/bin/env python3
"""
Example usage of OGD functions.
This shows how to integrate the functions into your notebook.
"""

# Import the functions
import sys
import os
sys.path.append(os.path.dirname(__file__))

from ogd_functions import (
    create_ogd_method_from_dataframe,
    find_spanish_electricity_activity,
    create_functional_unit,
    calculate_lcia_with_bw2calc,
    get_top_contributions,
    get_bottom_contributions,
    run_complete_workflow
)

import pandas as pd
import bw2data as bd

def main():
    """Example usage that you can copy into your notebook."""
    
    print("Setting up Brightway25...")
    project_name = "SurplusEx"
    if project_name not in bd.projects:
        bd.projects.create(project_name)
    bd.projects.set_current(project_name)
    
    print("=" * 80)
    print("EXAMPLE: How to use the OGD functions in your notebook")
    print("=" * 80)
    
    # ============================================
    # OPTION 1: Run the complete workflow
    # ============================================
    print("\n" + "=" * 80)
    print("OPTION 1: Complete workflow")
    print("=" * 80)
    
    # This does everything automatically
    results = run_complete_workflow(amount_twh=268)
    
    if results:
        # Access the results
        total_score = results['total_score']
        elementary_contributions = results['elementary_contributions']
        lca = results['lca']
        
        print(f"\nTotal score: {total_score}")
        print(f"Contributions DataFrame shape: {elementary_contributions.shape}")
    
    # ============================================
    # OPTION 2: Step-by-step usage
    # ============================================
    print("\n" + "=" * 80)
    print("OPTION 2: Step-by-step usage")
    print("=" * 80)
    
    # Step 1: Load your OGD data
    print("\nStep 1: Load OGD data")
    OGD_df = pd.read_excel('Ore-GradeDeclineConstants.xlsx')
    print(f"Loaded {len(OGD_df)} records")
    
    # Step 2: Create the OGD method
    print("\nStep 2: Create OGD method")
    method_object, method_data = create_ogd_method_from_dataframe(OGD_df)
    method_name_tuple = method_object.name
    print(f"Method created: {method_name_tuple}")
    
    # Step 3: Find Spanish electricity activity
    print("\nStep 3: Find Spanish electricity activity")
    electricity_activities = find_spanish_electricity_activity()
    electricity_activity = electricity_activities[0]  # Use first match
    print(f"Using: {electricity_activity.get('name')}")
    
    # Step 4: Create functional unit for 268 TWh
    print("\nStep 4: Create functional unit")
    fu, amount, unit_display = create_functional_unit(electricity_activity, amount_twh=268)
    print(f"Functional unit: {amount} {unit_display}")
    
    # Step 5: Calculate LCIA using bw2calc (no CSV files!)
    print("\nStep 5: Calculate LCIA with bw2calc")
    results = calculate_lcia_with_bw2calc(fu, method_name_tuple)
    
    if results:
        total_score = results['total_score']
        elementary_contributions = results['elementary_contributions']
        lca = results['lca']
        
        print(f"Total LCIA Score: {total_score}")
        print(f"Number of contributions: {len(elementary_contributions)}")
        
        # Get top and bottom contributions
        print("\nTop 5 contributions:")
        print(get_top_contributions(elementary_contributions, n=5))
        
        print("\nBottom 5 contributions:")
        print(get_bottom_contributions(elementary_contributions, n=5))
        
        # You can also access the LCA object for more analysis
        print(f"\nLCA object available: {type(lca)}")
        
        # Save results if needed
        elementary_contributions.to_csv('Results/EsElec/elementary_flow_contributions_bw2calc.csv', index=False)
        print("✅ Results saved to CSV")
    
    # ============================================
    # OPTION 3: Custom method name
    # ============================================
    print("\n" + "=" * 80)
    print("OPTION 3: Custom method name")
    print("=" * 80)
    
    # Create method with custom suffix
    method_object, method_data = create_ogd_method_from_dataframe(
        OGD_df, 
        method_name_suffix="Custom suffix for testing"
    )
    print(f"Method created with custom suffix: {method_object.name}")
    
    print("\n" + "=" * 80)
    print("EXAMPLE COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    main()