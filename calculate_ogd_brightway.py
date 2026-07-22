#!/usr/bin/env python3
"""
Script to calculate elementary flow contributions using Brightway25
and create a functional unit for 268 TWh of electricity production from high voltage Spain electricity.
"""

import os
import sys
import pandas as pd
import numpy as np
import bw2data as bd
import bw2calc as bc
from pathlib import Path

def setup_brightway_project():
    """Set up the Brightway25 project and ensure databases are available."""
    print("Setting up Brightway25 project...")
    
    # Set project name
    project_name = "SurplusEx"
    
    # Check if project exists, if not create it
    if project_name not in bd.projects:
        bd.projects.create(project_name)
    
    bd.projects.set_current(project_name)
    
    print(f"Current project: {bd.projects.current}")
    print(f"Available databases: {list(bd.databases)}")
    
    # Check if ecoinvent databases are available
    required_dbs = ['ecoinvent-3.4-biosphere', 'ecoinvent-3.4-cutoff']
    missing_dbs = [db for db in required_dbs if db not in bd.databases]
    
    if missing_dbs:
        print(f"Warning: Missing databases: {missing_dbs}")
        print("You may need to import ecoinvent data first.")
        return False
    
    return True

def load_ore_grade_data():
    """Load the ore grade decline constants from Excel file."""
    print("Loading ore grade decline data...")
    
    excel_path = Path("Ore-GradeDeclineConstants.xlsx")
    if not excel_path.exists():
        print(f"Error: File {excel_path} not found!")
        return None
    
    try:
        OGD_df = pd.read_excel(excel_path)
        print(f"Loaded {len(OGD_df)} ore grade decline records")
        
        # Remove gold as mentioned in the notebook
        OGD_df = OGD_df[OGD_df['Metal'] != "Gold"]
        print(f"After removing Gold: {len(OGD_df)} records")
        
        return OGD_df
    except Exception as e:
        print(f"Error loading ore grade data: {e}")
        return None

def calculate_cf1_dict(OGD_df):
    """Calculate CF1 dictionary from ore grade decline data."""
    print("Calculating CF1 values...")
    
    # Calculate CF1 using the formula from the notebook
    numerator = OGD_df['URR'] * OGD_df['beta'] * np.exp(OGD_df['alpha'])
    denominator = OGD_df['CME']**2.0
    
    OGD_df['CF1'] = -(numerator / denominator) * ((OGD_df['URR'] / OGD_df['CME']) - 1)**(OGD_df['beta'] - 1)
    
    # Create dictionary with element symbols as keys
    CF1_dict = dict(zip(OGD_df['Symbol'], OGD_df['CF1']))
    
    print(f"CF1 dictionary created with {len(CF1_dict)} elements")
    for elem, cf in list(CF1_dict.items())[:5]:
        print(f"  {elem}: {cf}")
    
    return CF1_dict

def create_lcia_method(CF1_dict, OGD_df):
    """Create and register the LCIA method in Brightway25."""
    print("Creating LCIA method...")
    
    # Define method name tuple
    method_name_tuple = (
        "Cumulative Ore Grade Decline",
        "Cumulative ore grade variation",
        f"Applied to {len(OGD_df)} elements"
    )
    
    # Define metadata
    method_metadata = {
        'unit': 'change in ore grade per kg of metal extracted',
        'description': 'This LCIA method is one out of the 3 steps of the currently developing surplus exergy method.'
                        'It models the decrease of ore-grade with the progression of the extraction activities.'
                        'Each characterisation factor answers the question: For every additional kg of metal extracted within the product system (increase in CMT), by how much does the ore grade (g) drop?'
                        'The impact score (IS) is not the final value of the intended impact yet. '
                        'This IS needs to be fed to two more calculations to find out the exergy lost due to the dissipation in the product system.',
        'source': 'The values are taken from the appendix of ReCiPe 2016: https://www.rivm.nl/bibliotheek/rapporten/2016-0104.pdf',
        'version': '2.0',
        'num_cfs': 0,  # Will be updated
        'application': 'Input product-system metals characterization'
    }
    
    # Get biosphere database
    biosphere_db = bd.Database('ecoinvent-3.4-biosphere')
    
    # Create method data by matching flows to CF1 values
    method_data = []
    
    print("Matching biosphere flows to CF1 values...")
    
    for flow in biosphere_db:
        # Only consider natural resource flows in kg
        if (isinstance(flow.get('categories'), tuple) and 
            len(flow['categories']) > 0 and 
            flow['unit'].lower() == 'kilogram' and 
            flow['categories'][0].lower() == 'natural resource'):
            
            flow_name = flow['name']
            
            # Try to match flow name to elements in CF1_dict
            # This is a simplified approach - you might need more sophisticated matching
            matched = False
            for elem in CF1_dict.keys():
                if elem in flow_name:
                    method_data.append((flow.key, CF1_dict[elem]))
                    matched = True
                    break
            
            if not matched:
                # Try to match by checking if any element symbol appears in the flow name
                for elem in CF1_dict.keys():
                    if elem.lower() in flow_name.lower():
                        method_data.append((flow.key, CF1_dict[elem]))
                        matched = True
                        break
    
    # Update metadata with actual number of CFs
    method_metadata['num_cfs'] = len(method_data)
    
    print(f"Created method data with {len(method_data)} characterization factors")
    
    # Create or load the Brightway2 Method object
    method_object = bd.Method(method_name_tuple)
    
    # Forcefully register/write the method
    try:
        method_object.register(**method_metadata)
        method_object.write(method_data)
        
        print(f"✅ Successfully {'overwrote' if method_name_tuple in bd.methods else 'created'} method: {method_name_tuple}")
        print(f"   - Unit: {method_metadata['unit']}")
        print(f"   - Number of CFs: {len(method_data)}")
        
        return method_object
        
    except Exception as e:
        print(f"❌ Failed to write method: {str(e)}")
        raise

def find_spanish_electricity():
    """Find the high voltage Spain electricity market activity."""
    print("Searching for Spanish electricity activity...")
    
    cutoff_db = bd.Database('ecoinvent-3.4-cutoff')
    
    # Search for Spanish electricity activities
    search_terms = ['electricity', 'spain', 'high voltage', 'main market']
    
    potential_activities = []
    
    for activity in cutoff_db:
        activity_name = activity.get('name', '').lower()
        if all(term in activity_name for term in ['electricity', 'spain']):
            potential_activities.append(activity)
    
    print(f"Found {len(potential_activities)} potential Spanish electricity activities:")
    for i, act in enumerate(potential_activities[:10]):  # Show first 10
        print(f"  {i+1}. {act.get('name')} - {act.get('reference product')} - {act.key}")
    
    if not potential_activities:
        print("No Spanish electricity activities found. Trying broader search...")
        for activity in cutoff_db:
            activity_name = activity.get('name', '').lower()
            if 'electricity' in activity_name and ('es' in activity_name or 'spain' in activity_name):
                potential_activities.append(activity)
        
        for i, act in enumerate(potential_activities[:10]):
            print(f"  {i+1}. {act.get('name')} - {act.get('reference product')} - {act.key}")
    
    return potential_activities

def create_functional_unit(electricity_activity):
    """Create a functional unit for 268 TWh of electricity production."""
    print("Creating functional unit...")
    
    # 268 TWh = 268 * 10^12 Wh = 268 * 10^9 kWh = 268 * 10^9 * 3600 kJ
    # But we need to convert to the unit of the activity
    
    # First, check the unit of the electricity activity
    activity_unit = electricity_activity.get('unit', '').lower()
    print(f"Electricity activity unit: {activity_unit}")
    
    # Convert 268 TWh to appropriate units
    # 1 TWh = 10^9 kWh = 10^12 Wh
    # Common units in ecoinvent: kWh, MJ, GJ
    
    if 'kwh' in activity_unit:
        amount = 268 * 10**9  # 268 TWh = 268 * 10^9 kWh
    elif 'mj' in activity_unit:
        amount = 268 * 10**9 * 3600 / 10**6  # 268 TWh = 268 * 10^9 kWh = 268 * 10^9 * 3600 MJ = 9.648 * 10^17 MJ
    elif 'gj' in activity_unit:
        amount = 268 * 10**9 * 3600 / 10**9  # 268 TWh = 268 * 10^9 * 3600 GJ = 9.648 * 10^14 GJ
    else:
        # Default to kWh if unit is unclear
        amount = 268 * 10**9
        print(f"Warning: Unknown unit '{activity_unit}', defaulting to kWh")
    
    print(f"Functional unit amount: {amount} {activity_unit}")
    
    # Create the functional unit as a dictionary
    fu = {electricity_activity.key: amount}
    
    return fu, amount

def calculate_lcia_score(fu, method_name_tuple):
    """Calculate the LCIA score for the functional unit."""
    print("Calculating LCIA score...")
    
    try:
        # Create LCA object
        lca = bc.LCA(fu, method_name_tuple)
        lca.lci()
        lca.lcia()
        
        score = lca.score
        print(f"LCIA Score: {score}")
        
        # Get inventory
        inventory = lca.inventory
        print(f"Inventory shape: {inventory.shape}")
        
        # Get characterization matrix
        characterization_matrix = lca.characterization_matrix
        print(f"Characterization matrix shape: {characterization_matrix.shape}")
        
        # Calculate elementary flow contributions
        if hasattr(lca, 'characterized_inventory'):
            characterized_inventory = lca.characterized_inventory
            print(f"Characterized inventory shape: {characterized_inventory.shape}")
            
            # Get the elementary flow contributions
            elementary_contributions = characterized_inventory.sum(axis=1)
            print(f"Elementary flow contributions (first 10):")
            for i in range(min(10, len(elementary_contributions))):
                if elementary_contributions[i] != 0:
                    flow_key = lca.inventory.rows[i]
                    flow = bd.get_activity(flow_key)
                    print(f"  {flow.get('name')}: {elementary_contributions[i]}")
        
        return score, lca
        
    except Exception as e:
        print(f"Error calculating LCIA score: {e}")
        return None, None

def save_results_to_csv(lca, method_name_tuple, filename="elementary_flow_contributions.csv"):
    """Save elementary flow contributions to CSV file."""
    print(f"Saving results to {filename}...")
    
    try:
        # Get the characterized inventory
        characterized_inventory = lca.characterized_inventory
        
        # Create a DataFrame with flow names and their contributions
        results_data = []
        
        for i, flow_key in enumerate(lca.inventory.rows):
            contribution = characterized_inventory[i, 0] if characterized_inventory.ndim > 1 else characterized_inventory[i]
            if contribution != 0:
                flow = bd.get_activity(flow_key)
                results_data.append({
                    'flow_key': flow_key,
                    'flow_name': flow.get('name', 'Unknown'),
                    'categories': str(flow.get('categories', '')),
                    'unit': flow.get('unit', ''),
                    'contribution': contribution
                })
        
        # Sort by absolute contribution
        results_df = pd.DataFrame(results_data)
        results_df['abs_contribution'] = results_df['contribution'].abs()
        results_df = results_df.sort_values('abs_contribution', ascending=False)
        
        # Save to CSV
        results_df.to_csv(filename, index=False)
        print(f"✅ Results saved to {filename}")
        
        return results_df
        
    except Exception as e:
        print(f"Error saving results: {e}")
        return None

def main():
    """Main function to execute the workflow."""
    print("=" * 60)
    print("ELEMENTARY FLOW CONTRIBUTION CALCULATION")
    print("Using Brightway25 for Ore Grade Decline Method")
    print("=" * 60)
    
    # Step 1: Set up Brightway project
    if not setup_brightway_project():
        print("Failed to set up Brightway project. Exiting.")
        return
    
    # Step 2: Load ore grade data
    OGD_df = load_ore_grade_data()
    if OGD_df is None:
        print("Failed to load ore grade data. Exiting.")
        return
    
    # Step 3: Calculate CF1 dictionary
    CF1_dict = calculate_cf1_dict(OGD_df)
    
    # Step 4: Create LCIA method
    method_object = create_lcia_method(CF1_dict, OGD_df)
    
    # Step 5: Find Spanish electricity activity
    electricity_activities = find_spanish_electricity()
    
    if not electricity_activities:
        print("No Spanish electricity activities found. Exiting.")
        return
    
    # For now, use the first activity found
    # In a real scenario, you would want to select the most appropriate one
    electricity_activity = electricity_activities[0]
    print(f"\nUsing electricity activity: {electricity_activity.get('name')}")
    
    # Step 6: Create functional unit
    fu, amount = create_functional_unit(electricity_activity)
    print(f"Functional unit: {amount} {electricity_activity.get('unit', 'units')} of {electricity_activity.get('name')}")
    
    # Step 7: Calculate LCIA score
    method_name_tuple = method_object.name
    score, lca = calculate_lcia_score(fu, method_name_tuple)
    
    if lca is not None:
        # Step 8: Save results
        results_df = save_results_to_csv(lca, method_name_tuple, "Results/EsElec/elementary_flow_contributions.csv")
        
        if results_df is not None:
            print(f"\nTop 10 elementary flow contributions:")
            print(results_df.head(10)[['flow_name', 'contribution']])
            
            # Also save the total score to the original format
            # Create a result similar to the existing EsS1.csv
            total_score_df = pd.DataFrame({
                'index': ['Score', 'Rest (-)'],
                'name': ['', ''],
                'categories': ['', ''],
                'type': ['', ''],
                'unit': [method_metadata['unit'], ''],
                'database': ['', ''],
                '0': [score, 0]  # Assuming rest is 0 for now
            })
            
            # Add the elementary flow contributions
            for _, row in results_df.iterrows():
                total_score_df = pd.concat([
                    total_score_df,
                    pd.DataFrame({
                        'index': [row['flow_key']],
                        'name': [row['flow_name']],
                        'categories': [row['categories']],
                        'type': ['natural resource'],
                        'unit': [method_metadata['unit']],
                        'database': ['ecoinvent-3.4-biosphere'],
                        '0': [row['contribution']]
                    })
                ], ignore_index=True)
            
            # Save to the same format as EsS1.csv
            total_score_df.to_csv('Results/EsElec/EsS1_automated.csv', index=False)
            print(f"✅ Also saved results to Results/EsElec/EsS1_automated.csv")
    
    print("\n" + "=" * 60)
    print("PROCESS COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    main()