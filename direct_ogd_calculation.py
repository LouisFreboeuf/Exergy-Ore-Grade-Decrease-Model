#!/usr/bin/env python3
"""
Direct script to:
1. Use Brightway25 to calculate elementary flow contributions from EsS1.csv
2. Create the LCIA method with your exact metadata
3. Build functional unit for 268 TWh of Spanish high voltage electricity
"""

import pandas as pd
import bw2data as bd
import bw2calc as bc
from pathlib import Path

def main():
    """Main function that does exactly what you requested."""
    
    print("Starting direct OGD calculation...")
    
    # Set up project
    project_name = "SurplusEx"
    if project_name not in bd.projects:
        bd.projects.create(project_name)
    bd.projects.set_current(project_name)
    
    # ============================================
    # STEP 1: Import data from EsS1.csv
    # ============================================
    print("\n1. Importing data from Results/EsElec/EsS1.csv")
    IS1_df = pd.read_csv('Results/EsElec/EsS1.csv')
    print(f"Loaded {len(IS1_df)} rows")
    print("First 3 rows:")
    print(IS1_df.head(3))
    
    # ============================================
    # STEP 2: Create the LCIA method with your metadata
    # ============================================
    print("\n2. Creating LCIA method with your specified metadata...")
    
    # Extract method data from the CSV (skip Score and Rest rows)
    method_data = []
    for _, row in IS1_df.iterrows():
        if row['index'] in ['Score', 'Rest (-)']:
            continue
        
        # The index contains: "name | categories | type | unit | database"
        index_parts = str(row['index']).split(' | ')
        if len(index_parts) >= 5:
            flow_name = index_parts[0]
            categories = eval(index_parts[1])  # Convert string to tuple
            
            # Try to find the flow in the biosphere database
            biosphere_db = bd.Database('ecoinvent-3.4-biosphere')
            for flow in biosphere_db:
                if flow['name'] == flow_name and flow['categories'] == categories:
                    method_data.append((flow.key, row['0']))
                    break
    
    print(f"Extracted {len(method_data)} characterization factors")
    
    # 1. Define the method name as a tuple for the desired hierarchy
    method_name_tuple = (
        "Cumulative Ore Grade Decline",
        "Cumulative ore grade variation",
        f"Applied to {len(method_data)} elements"  # Updated with actual count
    )

    # 2. Define metadata for the method, including the unit and a description
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

    # 3. Create or load the Brightway2 Method object
    method_object = bd.Method(method_name_tuple)

    # 4. Forcefully register/write the method
    try:
        # This will overwrite existing method
        method_object.register(**method_metadata) 
        method_object.write(method_data)
        
        print(f"\n✅ Successfully {'overwrote' if method_name_tuple in bd.methods else 'created'} method: {method_name_tuple}")
        print(f"   - Unit: {method_metadata['unit']}")
        print(f"   - Number of CFs: {len(method_data)}")
        
    except Exception as e:
        print(f"\n❌ Failed to write method: {str(e)}")
        raise

    # --- Verification ---
    print("\n--- Verification ---")
    if method_name_tuple in bd.methods:
        retrieved_method = bd.Method(method_name_tuple)
        loaded_data = retrieved_method.load()
        
        print(f"🔍 Method verification:")
        print(f"   Name: {retrieved_method.name}")
        print(f"   Metadata version: {retrieved_method.metadata.get('version', 'N/A')}")
        print(f"   Number of CFs loaded: {len(loaded_data)}")
        
        # Check for potential data loss
        if len(loaded_data) != len(method_data):
            print(f"⚠️  Warning: CF count mismatch. Expected {len(method_data)}, got {len(loaded_data)}")
        else:
            print("✅ CF count matches expected value")
            
        # Show sample CFs
        print("\nSample characterization factors (first 3):")
        for cf in loaded_data[:3]:
            flow = bd.get_activity(cf[0])
            print(f"   - {flow['name']}: {cf[1]}")
    else:
        print(f"❌ Error: Method {method_name_tuple} not found after writing attempt")

    print("\nProcess completed")
    
    # ============================================
    # STEP 3: Build the Functional Unit
    # ============================================
    print("\n3. Building functional unit for 268 TWh of Spanish high voltage electricity...")
    
    # Find Spanish high voltage electricity main market
    cutoff_db = bd.Database('ecoinvent-3.4-cutoff')
    
    spanish_electricity = None
    for activity in cutoff_db:
        name = activity.get('name', '').lower()
        if all(term in name for term in ['electricity', 'spain', 'high voltage', 'main market']):
            spanish_electricity = activity
            break
        elif all(term in name for term in ['electricity', 'es', 'high voltage']):
            spanish_electricity = activity
            break
    
    if spanish_electricity is None:
        print("❌ Could not find Spanish high voltage electricity main market activity")
        print("Available electricity activities in Spain:")
        for activity in cutoff_db:
            name = activity.get('name', '').lower()
            if 'electricity' in name and ('spain' in name or 'es' in name):
                print(f"  - {activity.get('name')} ({activity.key})")
        return
    
    print(f"Found activity: {spanish_electricity.get('name')}")
    print(f"Reference product: {spanish_electricity.get('reference product')}")
    print(f"Unit: {spanish_electricity.get('unit')}")
    
    # Create functional unit: 268 TWh
    # Convert TWh to the appropriate unit
    activity_unit = spanish_electricity.get('unit', '').lower()
    
    if 'kwh' in activity_unit:
        amount = 268 * 10**9  # 268 TWh = 268 * 10^9 kWh
    elif 'mj' in activity_unit:
        amount = 268 * 10**9 * 3600  # 268 TWh = 268 * 10^9 kWh = 268 * 10^9 * 3600 MJ
    elif 'gj' in activity_unit:
        amount = 268 * 10**9 * 3.6  # 268 TWh = 268 * 10^9 * 3.6 GJ
    else:
        amount = 268 * 10**9  # Default to kWh
        print(f"Warning: Unknown unit '{activity_unit}', defaulting to kWh")
    
    fu = {spanish_electricity.key: amount}
    print(f"Functional unit: {amount} {activity_unit} of {spanish_electricity.get('name')}")
    
    # ============================================
    # STEP 4: Calculate elementary flow contributions
    # ============================================
    print("\n4. Calculating elementary flow contributions...")
    
    try:
        # Create LCA object
        lca = bc.LCA(fu, method_name_tuple)
        lca.lci()
        lca.lcia()
        
        total_score = lca.score
        print(f"Total LCIA Score: {total_score}")
        
        # Get characterized inventory (elementary flow contributions)
        characterized_inventory = lca.characterized_inventory
        
        # Create results DataFrame
        results = []
        for i, flow_key in enumerate(lca.inventory.rows):
            contribution = characterized_inventory[i, 0] if characterized_inventory.ndim > 1 else characterized_inventory[i]
            if abs(contribution) > 1e-20:  # Filter out very small values
                flow = bd.get_activity(flow_key)
                results.append({
                    'flow_name': flow.get('name'),
                    'categories': str(flow.get('categories')),
                    'type': flow.get('type'),
                    'unit': flow.get('unit'),
                    'database': flow.get('database'),
                    'contribution': contribution
                })
        
        results_df = pd.DataFrame(results)
        results_df['abs_contribution'] = results_df['contribution'].abs()
        results_df = results_df.sort_values('abs_contribution', ascending=False)
        
        print(f"Found {len(results_df)} elementary flow contributions")
        
        # Save results
        output_path = 'Results/EsElec/EsS1_direct_calculation.csv'
        results_df.to_csv(output_path, index=False)
        print(f"✅ Results saved to {output_path}")
        
        # Show top contributions
        print("\nTop 10 elementary flow contributions:")
        for _, row in results_df.head(10).iterrows():
            print(f"  {row['flow_name']}: {row['contribution']}")
        
        # Also create a version in the same format as EsS1.csv
        output_df = pd.DataFrame({
            'index': ['Score', 'Rest (-)'],
            'name': ['', ''],
            'categories': ['', ''],
            'type': ['', ''],
            'unit': [method_metadata['unit'], ''],
            'database': ['', ''],
            '0': [total_score, 0]
        })
        
        for _, row in results_df.iterrows():
            index_str = f"{row['flow_name']} | {row['categories']} | {row['type']} | {row['unit']} | {row['database']}"
            output_df = pd.concat([
                output_df,
                pd.DataFrame({
                    'index': [index_str],
                    'name': [row['flow_name']],
                    'categories': [row['categories']],
                    'type': [row['type']],
                    'unit': [method_metadata['unit']],
                    'database': [row['database']],
                    '0': [row['contribution']]
                })
            ], ignore_index=True)
        
        automated_path = 'Results/EsElec/EsS1_automated_direct.csv'
        output_df.to_csv(automated_path, index=False)
        print(f"✅ Results in EsS1 format saved to {automated_path}")
        
    except Exception as e:
        print(f"❌ Error calculating LCIA: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("DIRECT CALCULATION COMPLETED")
    print("="*60)

if __name__ == "__main__":
    main()