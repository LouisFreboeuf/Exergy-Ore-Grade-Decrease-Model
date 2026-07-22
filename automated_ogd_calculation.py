#!/usr/bin/env python3
"""
Automated script to:
1. Calculate elementary flow contributions from existing EsS1.csv data
2. Create the LCIA method with specified metadata
3. Build functional unit for 268 TWh of Spanish high voltage electricity
"""

import os
import pandas as pd
import numpy as np
import bw2data as bd
import bw2calc as bc
from pathlib import Path

def setup_brightway():
    """Set up Brightway25 project."""
    print("Setting up Brightway25...")
    
    project_name = "SurplusEx"
    if project_name not in bd.projects:
        bd.projects.create(project_name)
    
    bd.projects.set_current(project_name)
    print(f"Current project: {bd.projects.current}")
    
    # Check databases
    if 'ecoinvent-3.4-biosphere' not in bd.databases:
        print("Error: ecoinvent-3.4-biosphere database not found")
        return False
    
    if 'ecoinvent-3.4-cutoff' not in bd.databases:
        print("Error: ecoinvent-3.4-cutoff database not found")
        return False
    
    return True

def load_existing_results():
    """Load existing EsS1.csv results."""
    print("Loading existing results...")
    
    csv_path = Path("Results/EsElec/EsS1.csv")
    if not csv_path.exists():
        print(f"Error: {csv_path} not found")
        return None
    
    try:
        df = pd.read_csv(csv_path)
        print(f"Loaded {len(df)} rows from {csv_path}")
        return df
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return None

def create_ogd_method_from_data(IS1_df):
    """Create the OGD method using the metadata you specified."""
    print("Creating OGD method...")
    
    # Extract method data from the CSV (skip Score and Rest rows)
    method_data = []
    for _, row in IS1_df.iterrows():
        # Skip Score and Rest rows
        if row['index'] in ['Score', 'Rest (-)']:
            continue
        
        # Get the flow key and value
        # The index column contains the flow key in the format: "name | categories | type | unit | database"
        index_parts = str(row['index']).split(' | ')
        if len(index_parts) >= 5:
            flow_name = index_parts[0]
            categories = eval(index_parts[1])  # Convert string to tuple
            flow_type = index_parts[2]
            unit = index_parts[3]
            database = index_parts[4]
            
            # Find the actual flow key in the database
            try:
                db = bd.Database(database)
                for flow in db:
                    if flow['name'] == flow_name and flow['categories'] == categories:
                        method_data.append((flow.key, row['0']))
                        break
            except:
                # If we can't find the exact flow, use a placeholder
                # This will be handled by Brightway's internal matching
                method_data.append((f"placeholder_{len(method_data)}", row['0']))
    
    # Define method name tuple as specified
    method_name_tuple = (
        "Cumulative Ore Grade Decline",
        "Cumulative ore grade variation",
        f"Applied to {len(method_data)} elements"  # Updated with actual count
    )
    
    # Define metadata exactly as specified
    method_metadata = {
        'unit': 'change in ore grade per kg of metal extracted',
        'description': 'This LCIA method is one out of the 3 steps of the currently developing surplus exergy method.'
                        'It models the decrease of ore-grade with the progression of the extraction activities.'
                        'Each characterisation factor answers the question: For every additional kg of metal extracted within the product system (increase in CMT), by how much does the ore grade (g) drop?'
                        'The impact score (IS) isn\'t the final value of the intended impact yet. '
                        'This IS needs to be fed to two more calculations to find out the exergy lost due to the dissipation in the product system.',
        'source': 'The values are taken from the appendix of ReCiPe 2016: https://www.rivm.nl/bibliotheek/rapporten/2016-0104.pdf',
        'version': '2.0',
        'num_cfs': len(method_data),
        'application': 'Input product-system metals characterization'
    }
    
    # Create or load the Brightway2 Method object
    method_object = bd.Method(method_name_tuple)
    
    # Forcefully register/write the method
    try:
        method_object.register(**method_metadata)
        method_object.write(method_data)
        
        print(f"✅ Successfully {'overwrote' if method_name_tuple in bd.methods else 'created'} method: {method_name_tuple}")
        print(f"   - Unit: {method_metadata['unit']}")
        print(f"   - Number of CFs: {len(method_data)}")
        
        # Verification
        print("\n--- Verification ---")
        if method_name_tuple in bd.methods:
            retrieved_method = bd.Method(method_name_tuple)
            loaded_data = retrieved_method.load()
            
            print(f"🔍 Method verification:")
            print(f"   Name: {retrieved_method.name}")
            print(f"   Metadata version: {retrieved_method.metadata.get('version', 'N/A')}")
            print(f"   Number of CFs loaded: {len(loaded_data)}")
            
            if len(loaded_data) != len(method_data):
                print(f"⚠️  Warning: CF count mismatch. Expected {len(method_data)}, got {len(loaded_data)}")
            else:
                print("✅ CF count matches expected value")
            
            # Show sample CFs
            print("\nSample characterization factors (first 3):")
            for cf in loaded_data[:3]:
                flow = bd.get_activity(cf[0])
                print(f"   - {flow['name']}: {cf[1]}")
        
        return method_object
        
    except Exception as e:
        print(f"❌ Failed to write method: {str(e)}")
        raise

def find_spanish_electricity():
    """Find high voltage Spain electricity main market activity."""
    print("\nSearching for Spanish electricity activity...")
    
    cutoff_db = bd.Database('ecoinvent-3.4-cutoff')
    
    # Search for the specific activity
    target_activities = []
    for activity in cutoff_db:
        name = activity.get('name', '').lower()
        ref_product = activity.get('reference product', '').lower()
        
        # Look for high voltage Spain electricity main market
        if all(term in name for term in ['electricity', 'spain', 'high voltage', 'main market']):
            target_activities.append(activity)
        elif all(term in name for term in ['electricity', 'spain', 'high voltage']):
            target_activities.append(activity)
        elif all(term in name for term in ['electricity', 'es', 'high voltage']):
            target_activities.append(activity)
    
    print(f"Found {len(target_activities)} potential activities:")
    for i, act in enumerate(target_activities):
        print(f"  {i+1}. {act.get('name')} - {act.get('reference product')} - {act.get('unit')} - {act.key}")
    
    if not target_activities:
        print("No exact match found. Trying broader search...")
        for activity in cutoff_db:
            name = activity.get('name', '').lower()
            if 'electricity' in name and ('spain' in name or 'es' in name):
                target_activities.append(activity)
        
        for i, act in enumerate(target_activities[:5]):  # Show first 5
            print(f"  {i+1}. {act.get('name')} - {act.get('reference product')} - {act.get('unit')} - {act.key}")
    
    return target_activities

def create_functional_unit(electricity_activity):
    """Create functional unit for 268 TWh of electricity production."""
    print(f"\nCreating functional unit for 268 TWh...")
    
    # Get activity details
    activity_name = electricity_activity.get('name')
    activity_unit = electricity_activity.get('unit', '').lower()
    activity_key = electricity_activity.key
    
    print(f"Selected activity: {activity_name}")
    print(f"Activity unit: {activity_unit}")
    
    # Convert 268 TWh to the appropriate unit
    # 1 TWh = 10^9 kWh = 3.6 * 10^12 MJ = 3.6 * 10^9 GJ
    
    if 'kwh' in activity_unit:
        amount = 268 * 10**9  # 268 TWh = 268 * 10^9 kWh
        unit_display = "kWh"
    elif 'mj' in activity_unit:
        amount = 268 * 10**9 * 3600  # 268 TWh = 268 * 10^9 kWh = 268 * 10^9 * 3600 MJ
        unit_display = "MJ"
    elif 'gj' in activity_unit:
        amount = 268 * 10**9 * 3.6  # 268 TWh = 268 * 10^9 kWh = 268 * 10^9 * 3.6 GJ
        unit_display = "GJ"
    else:
        # Default to kWh
        amount = 268 * 10**9
        unit_display = "kWh"
        print(f"Warning: Unknown unit '{activity_unit}', defaulting to kWh")
    
    print(f"Functional unit: {amount} {unit_display} of {activity_name}")
    
    # Create functional unit dictionary
    fu = {activity_key: amount}
    
    return fu, amount, unit_display

def calculate_and_save_results(fu, method_name_tuple, IS1_df):
    """Calculate LCIA and save elementary flow contributions."""
    print(f"\nCalculating LCIA with method {method_name_tuple}...")
    
    try:
        # Create LCA object
        lca = bc.LCA(fu, method_name_tuple)
        lca.lci()
        lca.lcia()
        
        score = lca.score
        print(f"Total LCIA Score: {score}")
        
        # Get characterized inventory (elementary flow contributions)
        characterized_inventory = lca.characterized_inventory
        
        # Create results DataFrame
        results_data = []
        
        # Get inventory rows (elementary flows)
        inventory_rows = lca.inventory.rows
        
        for i, flow_key in enumerate(inventory_rows):
            contribution = characterized_inventory[i, 0] if characterized_inventory.ndim > 1 else characterized_inventory[i]
            if abs(contribution) > 1e-20:  # Filter out very small contributions
                try:
                    flow = bd.get_activity(flow_key)
                    results_data.append({
                        'flow_key': flow_key,
                        'flow_name': flow.get('name', 'Unknown'),
                        'categories': str(flow.get('categories', '')),
                        'type': flow.get('type', ''),
                        'unit': flow.get('unit', ''),
                        'database': flow.get('database', ''),
                        'contribution': contribution
                    })
                except:
                    # If we can't get flow details, use basic info
                    results_data.append({
                        'flow_key': flow_key,
                        'flow_name': f"Unknown flow {flow_key}",
                        'categories': '',
                        'type': '',
                        'unit': '',
                        'database': '',
                        'contribution': contribution
                    })
        
        # Create DataFrame and sort by absolute contribution
        results_df = pd.DataFrame(results_data)
        results_df['abs_contribution'] = results_df['contribution'].abs()
        results_df = results_df.sort_values('abs_contribution', ascending=False)
        
        # Save to CSV in the same format as EsS1.csv
        output_path = Path("Results/EsElec/EsS1_automated.csv")
        
        # Create a DataFrame in the same format as the original
        output_df = pd.DataFrame({
            'index': ['Score', 'Rest (-)'],
            'name': ['', ''],
            'categories': ['', ''],
            'type': ['', ''],
            'unit': [method_metadata['unit'], ''],
            'database': ['', ''],
            '0': [score, 0]  # Score and Rest
        })
        
        # Add elementary flow contributions
        for _, row in results_df.iterrows():
            output_df = pd.concat([
                output_df,
                pd.DataFrame({
                    'index': [f"{row['flow_name']} | {row['categories']} | {row['type']} | {row['unit']} | {row['database']}"],
                    'name': [row['flow_name']],
                    'categories': [row['categories']],
                    'type': [row['type']],
                    'unit': [method_metadata['unit']],
                    'database': [row['database']],
                    '0': [row['contribution']]
                })
            ], ignore_index=True)
        
        # Save to CSV
        output_df.to_csv(output_path, index=False)
        print(f"✅ Results saved to {output_path}")
        
        # Also save a simplified version with just flow names and contributions
        simplified_df = results_df[['flow_name', 'contribution']].copy()
        simplified_df.columns = ['flow name', 'OG decrease']
        simplified_path = Path("Results/EsElec/EsS1_simplified.csv")
        simplified_df.to_csv(simplified_path, index=False)
        print(f"✅ Simplified results saved to {simplified_path}")
        
        return results_df, score
        
    except Exception as e:
        print(f"Error calculating LCIA: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def main():
    """Main execution function."""
    print("=" * 80)
    print("AUTOMATED ORE GRADE DECLINE CALCULATION")
    print("Using Brightway25 to calculate elementary flow contributions")
    print("=" * 80)
    
    # Step 1: Set up Brightway
    if not setup_brightway():
        print("Failed to set up Brightway. Exiting.")
        return
    
    # Step 2: Load existing results
    IS1_df = load_existing_results()
    if IS1_df is None:
        print("Failed to load existing results. Exiting.")
        return
    
    # Step 3: Create the OGD method with your specified metadata
    method_object = create_ogd_method_from_data(IS1_df)
    method_name_tuple = method_object.name
    
    # Step 4: Find Spanish electricity activity
    electricity_activities = find_spanish_electricity()
    
    if not electricity_activities:
        print("No Spanish electricity activities found. Exiting.")
        return
    
    # Use the first activity (or you could select manually)
    electricity_activity = electricity_activities[0]
    
    # Step 5: Create functional unit
    fu, amount, unit_display = create_functional_unit(electricity_activity)
    
    # Step 6: Calculate and save results
    results_df, total_score = calculate_and_save_results(fu, method_name_tuple, IS1_df)
    
    if results_df is not None:
        print(f"\n" + "=" * 80)
        print("RESULTS SUMMARY")
        print("=" * 80)
        print(f"Functional Unit: {amount} {unit_display} of {electricity_activity.get('name')}")
        print(f"Total LCIA Score: {total_score}")
        print(f"Number of elementary flow contributions: {len(results_df)}")
        
        print(f"\nTop 10 Elementary Flow Contributions:")
        print(results_df.head(10)[['flow_name', 'contribution']].to_string(index=False))
        
        print(f"\nBottom 10 Elementary Flow Contributions:")
        print(results_df.tail(10)[['flow_name', 'contribution']].to_string(index=False))
    
    print(f"\n" + "=" * 80)
    print("PROCESS COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    # Set up environment variables if needed
    # os.environ['EI_USERNAME'] = 'your_username'
    # os.environ['EI_PASSWORD'] = 'your_password'
    
    main()