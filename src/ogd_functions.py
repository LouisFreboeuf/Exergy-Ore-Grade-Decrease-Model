#!/usr/bin/env python3
"""
Functions for Ore Grade Decline calculations using Brightway25.
These functions can be imported and used directly in your notebook.
"""

import pandas as pd
import numpy as np
import bw2data as bd
import bw2calc as bc
from pathlib import Path
import re
from time import sleep
import time
import pubchempy as pcp
from pubchempy import PubChemHTTPError
from mendeleev import element


def clean_chemical_name(name):
    """Clean chemical names for better matching."""
    # Detect organic molecules (e.g. Ethane, 1,1-difluoro-, HFC-152a)
    pattern1 = r"^(.+?),\\s+(.+?)-(?:,\\s+.*|$)"
    # Detect flows with a comma
    pattern2 = r"(?<=[a-zA-Z]),.*"
    
    # First, check if the flow satisfies pattern1
    match = re.search(pattern1, name)
    if match:
        name = re.sub(pattern1, r"\\g<2>\\g<1>", name)
    else:
        name = re.sub(pattern2, "", name)
    
    # Remove Roman numerals at the end
    name = re.sub(r"\\s+[IVXLCDM]+$", "", name)
    
    # Remove 'ion' or 'ions' at the end
    name = re.sub(r"\\s+ions?$", "", name, flags=re.IGNORECASE)
    
    return name.strip()


def chem_comp(mf):
    """Parse molecular formula into element-count pairs."""
    pattern = r"([A-Z][a-z]?)(\\d*)"
    matches = re.findall(pattern, mf)
    
    parts = []
    for elem, count in matches:
        count = int(count) if count else 1
        parts.append([elem, count])
    
    return parts


def has_elem(parts, dict):
    """Check if any element in parts is in the dictionary."""
    for elem, count in parts:
        if elem not in dict.keys():
            continue
        else:
            return True
    return None


def cf_calculator(dict, mw, parts):
    """Calculate characterization factor for a molecular formula."""
    cf = 0
    for elem, count in parts:
        if elem in dict.keys():
            el_data = element(elem)
            aw = getattr(el_data, "atomic_weight", None)
            if aw is None:
                raise ValueError(f"No atomic_weight for element {elem}")
            
            # Handle different types of atomic_weight
            if hasattr(aw, "iloc"):
                aw = aw.iloc[0]
            elif hasattr(aw, "__array__") and not isinstance(aw, (float, int, str)):
                aw = aw[0]
            
            mass = float(aw)
            if mass == 0:
                raise ValueError(f"Atomic weight for {elem} is zero")
            
            # Compute contribution
            cf += count * (mass / mw) * dict[elem]
        else:
            continue
    return cf


def create_ogd_method_from_dataframe(OGD_df, method_name_suffix=None):
    """
    Create OGD method from OGD_df DataFrame.
    
    Parameters:
    -----------
    OGD_df : pandas.DataFrame
        DataFrame containing ore grade decline data with columns:
        Metal, Symbol, alpha, beta, URR, CME, k, CF1
    method_name_suffix : str, optional
        Custom suffix for method name. If None, uses element count.
    
    Returns:
    --------
    method_object : bw2data.Method
        The created Brightway25 method object
    method_data : list
        List of (flow_key, cf) tuples
    """
    print("Creating OGD method from DataFrame...")
    
    # Calculate CF1 if not already present
    if 'CF1' not in OGD_df.columns:
        numerator = OGD_df['URR'] * OGD_df['beta'] * np.exp(OGD_df['alpha'])
        denominator = OGD_df['CME']**2.0
        OGD_df['CF1'] = -(numerator / denominator) * ((OGD_df['URR'] / OGD_df['CME']) - 1)**(OGD_df['beta'] - 1)
    
    # Remove gold as mentioned in notebook
    OGD_df = OGD_df[OGD_df['Metal'] != "Gold"]
    
    # Create CF1 dictionary
    CF1_dict = dict(zip(OGD_df['Symbol'], OGD_df['CF1']))
    
    # Define method name - use number of ELEMENTS, not CFs
    num_elements = len(OGD_df)
    suffix = method_name_suffix or f"Applied to {num_elements} elements"
    
    method_name_tuple = (
        "Cumulative Ore Grade Decline",
        "Cumulative ore grade variation",
        suffix
    )
    
    # Define metadata
    method_metadata = {
        'unit': 'change in ore grade per kg of metal extracted',
        'description': 'This LCIA method is one out of the 3 steps of the currently developing surplus exergy method.'
                        'It models the decrease of ore-grade with the progression of the extraction activities.'
                        'Each characterisation factor answers the question: For every additional kg of metal extracted within the product system (increase in CMT), by how much does the ore grade (g) drop?'
                        'The impact score (IS) isn\'t the final value of the intended impact yet. '
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
    
    print(f"Matching {len(biosphere_db)} biosphere flows to {len(CF1_dict)} elements...")
    
    for flow in biosphere_db:
        # Only consider natural resource flows in kg
        if (isinstance(flow.get('categories'), tuple) and 
            len(flow['categories']) > 0 and 
            flow['unit'].lower() == 'kilogram' and 
            flow['categories'][0].lower() == 'natural resource'):
            
            flow_name_cleaned = clean_chemical_name(flow['name'])
            
            sleep(0.3)  # Slow down API requests
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    compound = pcp.get_compounds(flow_name_cleaned, 'name')
                    if compound is not None and len(compound) > 0:
                        c = compound[0]
                        mf = c.molecular_formula
                        mw = c.molecular_weight
                        
                        parts = chem_comp(mf)
                        
                        # If the flow contains only one element
                        if len(parts) == 1:
                            if has_elem(parts, CF1_dict):
                                cf = CF1_dict.get(parts[0][0])
                                method_data.append((flow.key, float(cf)))
                                break
                            else:
                                break
                        # If the flow contains a compound
                        elif len(parts) > 1:
                            if has_elem(parts, CF1_dict):
                                cf = cf_calculator(CF1_dict, mw, parts)
                                method_data.append((flow.key, float(cf)))
                                break
                            else:
                                break
                    else:
                        break
                        
                except PubChemHTTPError as e:
                    if "502" in str(e) and attempt < max_retries - 1:
                        print(f"Server hit a 502 for {flow_name_cleaned}. Retrying...")
                        time.sleep(2)
                    else:
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
        print(f"   - Based on {num_elements} elements")
        
        return method_object, method_data
        
    except Exception as e:
        print(f"❌ Failed to write method: {str(e)}")
        raise


def find_spanish_electricity_activity():
    """
    Find high voltage Spain electricity main market activity.
    
    Returns:
    --------
    list : List of matching activities
    """
    print("Searching for Spanish electricity activity...")
    
    cutoff_db = bd.Database('ecoinvent-3.4-cutoff')
    
    # Search for the specific activity
    target_activities = []
    for activity in cutoff_db:
        name = activity.get('name', '').lower()
        
        # Look for high voltage Spain electricity main market
        if all(term in name for term in ['electricity', 'spain', 'high voltage', 'main market']):
            target_activities.append(activity)
        elif all(term in name for term in ['electricity', 'es', 'high voltage']):
            target_activities.append(activity)
    
    print(f"Found {len(target_activities)} potential activities:")
    for i, act in enumerate(target_activities):
        print(f"  {i+1}. {act.get('name')} - {act.get('reference product')} - {act.get('unit')} - {act.key}")
    
    return target_activities


def create_functional_unit(electricity_activity, amount_twh=268):
    """
    Create functional unit for electricity production.
    
    Parameters:
    -----------
    electricity_activity : dict
        The Brightway25 activity for electricity
    amount_twh : float
        Amount in TWh (default: 268)
    
    Returns:
    --------
    fu : dict
        Functional unit dictionary {activity_key: amount}
    amount : float
        The converted amount in the activity's units
    unit_display : str
        The unit used for display
    """
    activity_name = electricity_activity.get('name')
    activity_unit = electricity_activity.get('unit', '').lower()
    activity_key = electricity_activity.key
    
    print(f"Creating functional unit for {amount_twh} TWh...")
    print(f"Activity: {activity_name}")
    print(f"Activity unit: {activity_unit}")
    
    # Convert TWh to the appropriate unit
    # 1 TWh = 10^9 kWh = 3.6 * 10^12 MJ = 3.6 * 10^9 GJ
    
    if 'kwh' in activity_unit:
        amount = amount_twh * 10**9  # TWh to kWh
        unit_display = "kWh"
    elif 'mj' in activity_unit:
        amount = amount_twh * 10**9 * 3600  # TWh to MJ
        unit_display = "MJ"
    elif 'gj' in activity_unit:
        amount = amount_twh * 10**9 * 3.6  # TWh to GJ
        unit_display = "GJ"
    else:
        # Default to kWh
        amount = amount_twh * 10**9
        unit_display = "kWh"
        print(f"Warning: Unknown unit '{activity_unit}', defaulting to kWh")
    
    print(f"Functional unit: {amount} {unit_display} of {activity_name}")
    
    # Create functional unit dictionary
    fu = {activity_key: amount}
    
    return fu, amount, unit_display


def calculate_lcia_with_bw2calc(fu, method_name_tuple):
    """
    Calculate LCIA using bw2calc directly (no CSV files).
    
    Parameters:
    -----------
    fu : dict
        Functional unit dictionary
    method_name_tuple : tuple
        Method name tuple
    
    Returns:
    --------
    results : dict
        Dictionary containing:
        - 'total_score': float, total LCIA score
        - 'elementary_contributions': DataFrame, elementary flow contributions
        - 'lca': LCA object, the LCA object for further analysis
    """
    print(f"Calculating LCIA with method {method_name_tuple}...")
    
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
        results_data = []
        for i, flow_key in enumerate(lca.inventory.rows):
            contribution = characterized_inventory[i, 0] if characterized_inventory.ndim > 1 else characterized_inventory[i]
            if abs(contribution) > 1e-20:  # Filter out very small values
                try:
                    flow = bd.get_activity(flow_key)
                    results_data.append({
                        'flow_key': flow_key,
                        'flow_name': flow.get('name'),
                        'categories': str(flow.get('categories')),
                        'type': flow.get('type'),
                        'unit': flow.get('unit'),
                        'database': flow.get('database'),
                        'contribution': contribution
                    })
                except:
                    results_data.append({
                        'flow_key': flow_key,
                        'flow_name': f"Unknown flow {flow_key}",
                        'categories': '',
                        'type': '',
                        'unit': '',
                        'database': '',
                        'contribution': contribution
                    })
        
        elementary_contributions = pd.DataFrame(results_data)
        elementary_contributions['abs_contribution'] = elementary_contributions['contribution'].abs()
        elementary_contributions = elementary_contributions.sort_values('abs_contribution', ascending=False)
        
        print(f"Found {len(elementary_contributions)} elementary flow contributions")
        
        return {
            'total_score': total_score,
            'elementary_contributions': elementary_contributions,
            'lca': lca
        }
        
    except Exception as e:
        print(f"❌ Error calculating LCIA: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_top_contributions(elementary_contributions, n=10):
    """Get top N contributions as a formatted string."""
    return elementary_contributions.head(n)[['flow_name', 'contribution']].to_string(index=False)


def get_bottom_contributions(elementary_contributions, n=10):
    """Get bottom N contributions as a formatted string."""
    return elementary_contributions.tail(n)[['flow_name', 'contribution']].to_string(index=False)


# Example usage function

def run_complete_workflow(OGD_df_path='Ore-GradeDeclineConstants.xlsx', amount_twh=268):
    """
    Complete workflow example that you can use in your notebook.
    
    Parameters:
    -----------
    OGD_df_path : str
        Path to Ore-GradeDeclineConstants.xlsx
    amount_twh : float
        Amount in TWh for functional unit (default: 268)
    
    Returns:
    --------
    results : dict
        Complete results dictionary
    """
    print("=" * 80)
    print("COMPLETE OGD WORKFLOW")
    print("=" * 80)
    
    # Step 1: Load OGD data
    print("\n1. Loading OGD data...")
    OGD_df = pd.read_excel(OGD_df_path)
    print(f"Loaded {len(OGD_df)} records")
    
    # Step 2: Create OGD method
    print("\n2. Creating OGD method...")
    method_object, method_data = create_ogd_method_from_dataframe(OGD_df)
    method_name_tuple = method_object.name
    
    # Step 3: Find Spanish electricity
    print("\n3. Finding Spanish electricity activity...")
    electricity_activities = find_spanish_electricity_activity()
    
    if not electricity_activities:
        print("No Spanish electricity activities found!")
        return None
    
    electricity_activity = electricity_activities[0]  # Use first match
    
    # Step 4: Create functional unit
    print("\n4. Creating functional unit...")
    fu, amount, unit_display = create_functional_unit(electricity_activity, amount_twh)
    
    # Step 5: Calculate LCIA
    print("\n5. Calculating LCIA...")
    results = calculate_lcia_with_bw2calc(fu, method_name_tuple)
    
    if results:
        print(f"\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)
        print(f"Functional Unit: {amount} {unit_display}")
        print(f"Total LCIA Score: {results['total_score']}")
        print(f"Number of elementary flow contributions: {len(results['elementary_contributions'])}")
        
        print(f"\nTop 10 Elementary Flow Contributions:")
        print(get_top_contributions(results['elementary_contributions']))
        
        print(f"\nBottom 10 Elementary Flow Contributions:")
        print(get_bottom_contributions(results['elementary_contributions']))
    
    return results