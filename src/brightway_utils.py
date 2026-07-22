#!/usr/bin/env python3
"""
Utility functions for Brightway25 activity searching and LCA operations.
These functions can be imported and used directly in your notebook.
"""

import bw2data as bd
import bw2calc as bc
import pandas as pd
import numpy as np


def search_activities(name=None, location=None, database=None, reference_product=None, limit=10):
    """
    Generic function to search for activities in Brightway25 databases.
    
    Parameters:
    -----------
    name : str, optional
        Activity name to search for (case insensitive, partial match)
    location : str, optional
        Location to filter by (case insensitive, partial match)
    database : str, optional
        Database name to search in (default: all databases)
    reference_product : str, optional
        Reference product to filter by (case insensitive, partial match)
    limit : int
        Maximum number of results to return (default: 10)
    
    Returns:
    --------
    list : List of matching activities
    """
    print(f"Searching for activities: name='{name}', location='{location}', database='{database}'")
    
    matching_activities = []
    
    # Determine which databases to search
    if database:
        databases_to_search = [database] if database in bd.databases else []
    else:
        databases_to_search = list(bd.databases)
    
    if not databases_to_search:
        print(f"Database '{database}' not found. Available databases: {list(bd.databases)}")
        return matching_activities
    
    # Search through each database
    for db_name in databases_to_search:
        try:
            db = bd.Database(db_name)
            
            for activity in db:
                # Check name match
                name_match = True
                if name:
                    activity_name = activity.get('name', '').lower()
                    name_match = name.lower() in activity_name
                
                # Check location match
                location_match = True
                if location:
                    activity_location = activity.get('location', '').lower()
                    location_match = location.lower() in activity_location
                
                # Check reference product match
                ref_product_match = True
                if reference_product:
                    activity_ref_product = activity.get('reference product', '').lower()
                    ref_product_match = reference_product.lower() in activity_ref_product
                
                # If all filters match, add to results
                if name_match and location_match and ref_product_match:
                    matching_activities.append(activity)
                    
                    # Stop if we've reached the limit
                    if len(matching_activities) >= limit:
                        break
                        
        except Exception as e:
            print(f"Error searching database {db_name}: {e}")
            continue
    
    print(f"Found {len(matching_activities)} matching activities")
    
    # Sort by relevance (exact matches first)
    if name:
        matching_activities.sort(key=lambda x: (
            0 if name.lower() == x.get('name', '').lower() else 1,
            x.get('name', '')
        ))
    
    return matching_activities


def find_spanish_electricity():
    """
    Find Spanish high voltage electricity activities.
    
    Returns:
    --------
    list : List of matching Spanish electricity activities
    """
    print("Searching for Spanish electricity activities...")
    
    # Search for electricity activities in Spain
    electricity_activities = search_activities(
        name='electricity',
        location='spain',
        limit=20
    )
    
    # If no results, try with 'es' location
    if not electricity_activities:
        electricity_activities = search_activities(
            name='electricity',
            location='es',
            limit=20
        )
    
    # Filter for high voltage and main market
    high_voltage_activities = []
    for activity in electricity_activities:
        activity_name = activity.get('name', '').lower()
        if ('high voltage' in activity_name and 'main market' in activity_name) or \
           ('high voltage' in activity_name and 'market' in activity_name):
            high_voltage_activities.append(activity)
    
    if high_voltage_activities:
        print(f"Found {len(high_voltage_activities)} high voltage Spanish electricity activities")
        for i, act in enumerate(high_voltage_activities):
            print(f"  {i+1}. {act.get('name')} - {act.get('reference product')} - {act.get('unit')} - {act.key}")
    else:
        print(f"Found {len(electricity_activities)} Spanish electricity activities (not all high voltage):")
        for i, act in enumerate(electricity_activities[:10]):  # Show first 10
            print(f"  {i+1}. {act.get('name')} - {act.get('reference product')} - {act.get('unit')} - {act.key}")
    
    return high_voltage_activities or electricity_activities


def get_activity_by_name_and_location(name, location, database=None):
    """
    Get a specific activity by name and location.
    
    Parameters:
    -----------
    name : str
        Activity name to search for
    location : str
        Location to filter by
    database : str, optional
        Database to search in (default: all databases)
    
    Returns:
    --------
    activity : dict or None
        The matching activity, or None if not found
    """
    activities = search_activities(name=name, location=location, database=database, limit=1)
    return activities[0] if activities else None


def get_inventory_flows(fu_dict, method=None):
    """
    Retrieve inventory flows from a functional unit using bw2calc.
    
    Parameters:
    -----------
    fu_dict : dict
        Functional unit dictionary {activity_key: amount}
    method : tuple, optional
        Method name tuple for LCIA calculation
    
    Returns:
    --------
    inventory_df : pandas.DataFrame
        DataFrame with inventory flows and amounts
    """
    print("Retrieving inventory flows...")
    
    try:
        # Create LCA object
        lca = bc.LCA(fu_dict)
        lca.lci()
        
        # Get inventory
        inventory = lca.inventory.sum(axis=1)
        if hasattr(inventory, 'A1'):
            inventory = inventory.A1
        
        # Get biosphere dictionary for reverse lookup
        reverse_dict = {v: k for k, v in lca.biosphere_dict.items()}
        
        # Find non-zero indices
        non_zero_indices = np.where(np.abs(inventory) > 1e-20)[0]
        
        all_flows = []
        for idx in non_zero_indices:
            amount = inventory[idx]
            flow_key = reverse_dict.get(idx)
            if flow_key:
                try:
                    flow = bd.get_activity(flow_key)
                    all_flows.append({
                        'Flow Key': flow_key,
                        'Flow Name': flow.get('name', 'Unknown'),
                        'Amount': amount,
                        'Unit': flow.get('unit', 'Unknown'),
                        'Categories': flow.get('categories', ()),
                        'Type': flow.get('type', 'Unknown'),
                        'Database': flow.get('database', 'Unknown')
                    })
                except Exception as e:
                    print(f"Error getting flow {flow_key}: {e}")
                    all_flows.append({
                        'Flow Key': flow_key,
                        'Flow Name': f"Unknown flow {flow_key}",
                        'Amount': amount,
                        'Unit': 'Unknown',
                        'Categories': (),
                        'Type': 'Unknown',
                        'Database': 'Unknown'
                    })
        
        inventory_df = pd.DataFrame(all_flows) if all_flows else pd.DataFrame()
        
        # Sort by absolute amount
        if not inventory_df.empty:
            inventory_df['Abs_Amount'] = inventory_df['Amount'].abs()
            inventory_df = inventory_df.sort_values('Abs_Amount', ascending=False)
        
        print(f"Found {len(inventory_df)} inventory flows")
        return inventory_df
        
    except Exception as e:
        print(f"Error retrieving inventory flows: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


def get_elementary_flow_contributions(fu_dict, method_name_tuple):
    """
    Get elementary flow contributions for a given functional unit and method.
    
    Parameters:
    -----------
    fu_dict : dict
        Functional unit dictionary {activity_key: amount}
    method_name_tuple : tuple
        Method name tuple for LCIA calculation
    
    Returns:
    --------
    contributions_df : pandas.DataFrame
        DataFrame with elementary flow contributions
    total_score : float
        Total LCIA score
    """
    print(f"Calculating elementary flow contributions for method {method_name_tuple}...")
    
    try:
        # Create LCA object
        lca = bc.LCA(fu_dict, method_name_tuple)
        lca.lci()
        lca.lcia()
        
        total_score = lca.score
        
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
                        'Flow Key': flow_key,
                        'Flow Name': flow.get('name', 'Unknown'),
                        'Categories': str(flow.get('categories', ())),
                        'Type': flow.get('type', 'Unknown'),
                        'Unit': flow.get('unit', 'Unknown'),
                        'Database': flow.get('database', 'Unknown'),
                        'Contribution': contribution
                    })
                except Exception as e:
                    results_data.append({
                        'Flow Key': flow_key,
                        'Flow Name': f"Unknown flow {flow_key}",
                        'Categories': '',
                        'Type': 'Unknown',
                        'Unit': 'Unknown',
                        'Database': 'Unknown',
                        'Contribution': contribution
                    })
        
        contributions_df = pd.DataFrame(results_data)
        
        # Add absolute contribution for sorting
        if not contributions_df.empty:
            contributions_df['Abs_Contribution'] = contributions_df['Contribution'].abs()
            contributions_df = contributions_df.sort_values('Abs_Contribution', ascending=False)
        
        print(f"Found {len(contributions_df)} elementary flow contributions")
        print(f"Total LCIA Score: {total_score}")
        
        return contributions_df, total_score
        
    except Exception as e:
        print(f"Error calculating elementary flow contributions: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame(), 0.0


def create_functional_unit(activity, amount_twh=268):
    """
    Create functional unit for electricity production.
    
    Parameters:
    -----------
    activity : dict
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
    activity_name = activity.get('name')
    activity_unit = activity.get('unit', '').lower()
    activity_key = activity.key
    
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