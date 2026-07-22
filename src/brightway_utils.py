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


def create_functional_unit(activity, amount, unit=None):
    """
    Create a functional unit dictionary.
    
    Parameters:
    -----------
    activity : dict
        Brightway25 activity
    amount : float
        Amount for the functional unit
    unit : str, optional
        Target unit (if different from activity unit)
    
    Returns:
    --------
    fu_dict : dict
        Functional unit dictionary {activity_key: amount}
    """
    activity_key = activity.key
    activity_unit = activity.get('unit', '').lower()
    
    # If target unit is specified and different from activity unit, convert
    if unit and unit.lower() != activity_unit:
        # Simple unit conversion (extend as needed)
        if 'kilowatt hour' in activity_unit and 'megajoule' in unit.lower():
            amount = amount * 3600  # kWh to MJ
        elif 'megajoule' in activity_unit and 'kilowatt hour' in unit.lower():
            amount = amount / 3600  # MJ to kWh
        elif 'gigajoule' in activity_unit and 'kilowatt hour' in unit.lower():
            amount = amount * 1000 * 3600  # GJ to kWh
        elif 'kilowatt hour' in activity_unit and 'gigajoule' in unit.lower():
            amount = amount / (1000 * 3600)  # kWh to GJ
        elif 'kilowatt hour' in activity_unit and 'terawatt hour' in unit.lower():
            amount = amount * 10**9  # kWh to TWh
    
    return {activity_key: amount}


# Example usage function

def example_usage():
    """Example of how to use these functions in your notebook."""
    
    print("=" * 80)
    print("BRIGHTWAY UTILS EXAMPLE USAGE")
    print("=" * 80)
    
    # Set up project
    project_name = "SurplusEx"
    if project_name not in bd.projects:
        bd.projects.create(project_name)
    bd.projects.set_current(project_name)
    
    # Example 1: Search for activities
    print("\n1. Search for activities by name and location:")
    activities = search_activities(name='electricity', location='spain', limit=5)
    for i, act in enumerate(activities):
        print(f"  {i+1}. {act.get('name')} - {act.get('location')} - {act.get('reference product')}")
    
    # Example 2: Find Spanish electricity
    print("\n2. Find Spanish electricity activities:")
    spanish_electricity = find_spanish_electricity()
    if spanish_electricity:
        print(f"  Found: {spanish_electricity[0].get('name')}")
    
    # Example 3: Get inventory flows
    print("\n3. Get inventory flows:")
    if spanish_electricity:
        # Create functional unit for 268 TWh
        fu = create_functional_unit(spanish_electricity[0], amount=268 * 10**9)  # 268 TWh = 268 * 10^9 kWh
        
        # Get inventory flows
        inventory_df = get_inventory_flows(fu)
        if not inventory_df.empty:
            print(f"  Found {len(inventory_df)} inventory flows")
            print("  Top 5 flows:")
            print(inventory_df.head()[['Flow Name', 'Amount', 'Unit']].to_string(index=False))
    
    # Example 4: Get elementary flow contributions
    print("\n4. Get elementary flow contributions:")
    if spanish_electricity:
        # You would need to have a method created first
        # For now, just show the function signature
        print("  Function: get_elementary_flow_contributions(fu_dict, method_name_tuple)")
        print("  Example: contributions_df, total_score = get_elementary_flow_contributions(fu, method_tuple)")
    
    print("\n" + "=" * 80)
    print("EXAMPLE COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    example_usage()