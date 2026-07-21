"""
LCA Automation for Exergy Ore Grade Decrease Model

This module provides automated functions for:
1. Running LCA on electricity production
2. Calculating characterization factors
3. Managing Brightway2 methods dynamically
"""

import numpy as np
import pandas as pd
import bw2data as bd
import bw2calc as bc
from mendeleev import element


def run_lca_electricity(country='ES', voltage='high'):
    """
    Run LCA for electricity production in a specific country.
    
    Args:
        country (str): Country code ('ES' for Spain, 'FR' for France)
        voltage (str): Voltage level ('high', 'medium', 'low')
    
    Returns:
        tuple: (lca_object, inventory, elementary_flow_contributions)
    """
    # Define the functional unit
    if voltage == 'high':
        activity_name = f'market for electricity, high voltage, {country}'
    else:
        activity_name = f'market for electricity, {voltage} voltage, {country}'
    
    try:
        # Get the activity
        activity = bd.Database('ecoinvent 3.4 cutoff').search(activity_name)
        if not activity:
            # Try alternative naming
            activity = bd.Database('ecoinvent 3.4 cutoff').search(
                f'electricity, {voltage} voltage, {country}'
            )
        
        if not activity:
            raise ValueError(f"Could not find activity: {activity_name}")
        
        # Use the first match
        activity_key = activity[0]
        
        # Create LCA object
        method = ('IPCC 2021', 'GWP 100a', 'climate change')  # Default method for testing
        lca = bc.LCA({activity_key: 1}, method=method)
        lca.lci()
        lca.lcia()
        
        # Get elementary flow contributions
        inventory = lca.inventory
        
        # Get biosphere flows and their amounts
        elementary_flows = []
        for flow_key, amount in inventory.items():
            flow = bd.get_activity(flow_key)
            if flow and 'biosphere' in flow['database']:
                elementary_flows.append({
                    'flow_key': flow_key,
                    'flow_name': flow['name'],
                    'amount': amount,
                    'database': flow['database'],
                    'code': flow['code']
                })
        
        ef_df = pd.DataFrame(elementary_flows)
        
        return lca, inventory, ef_df
        
    except Exception as e:
        print(f"Error running LCA: {e}")
        return None, None, pd.DataFrame()


def get_elementary_flow_contributions(activity_key, method=None):
    """
    Get elementary flow contributions for a given activity.
    
    Args:
        activity_key (tuple): Brightway2 activity key
        method (tuple): LCIA method tuple (optional)
    
    Returns:
        pd.DataFrame: Elementary flow contributions
    """
    # Create LCA object
    lca = bc.LCA({activity_key: 1}, method=method) if method else bc.LCA({activity_key: 1})
    lca.lci()
    
    # Get inventory
    inventory = lca.inventory
    
    # Extract elementary flows
    elementary_flows = []
    for flow_key, amount in inventory.items():
        flow = bd.get_activity(flow_key)
        if flow and 'biosphere' in flow['database']:
            elementary_flows.append({
                'flow_key': flow_key,
                'flow_name': flow['name'],
                'amount': amount,
                'unit': flow.get('unit', 'kg'),
                'database': flow['database'],
                'code': flow['code']
            })
    
    return pd.DataFrame(elementary_flows)


def calculate_characterization_factors(ogd_df, combined_is_df, option='ERC'):
    """
    Calculate characterization factors for ore grade decline.
    
    Args:
        ogd_df (pd.DataFrame): Ore Grade Decline constants DataFrame
        combined_is_df (pd.DataFrame): Combined impact score DataFrame
        option (str): 'ERC' or 'bc' for different calculation methods
    
    Returns:
        pd.DataFrame: DataFrame with added characterization factor columns
    """
    # Make copies to avoid modifying originals
    ogd_df = ogd_df.copy()
    combined_is_df = combined_is_df.copy()
    
    # Step 1: Calculate initial concentration for each mine
    def og_ini(alpha, beta, URR, CME):
        xi = np.exp(alpha) * ((URR / CME) - 1) ** beta
        return xi
    
    xi_list = []
    for index, row in ogd_df.iterrows():
        xi = og_ini(row['alpha'], row['beta'], row['URR'], row['CME'])
        xi_list.append(xi)
    ogd_df['Initial Concentration'] = xi_list
    
    # Step 2: Add initial concentration to combined_IS_df
    for index, row in combined_is_df.iterrows():
        xi = ogd_df[ogd_df['Metal'] == row['flow name']]['Initial Concentration']
        if len(xi) > 0:
            combined_is_df.at[index, 'Initial Concentration'] = xi.iloc[0]
    
    # Step 3: Add k values
    for index, row in combined_is_df.iterrows():
        k = ogd_df[ogd_df['Metal'] == row['flow name']]['k']
        if len(k) > 0:
            combined_is_df.at[index, 'k'] = k.iloc[0]
    
    # Step 4: Add symbols dynamically based on flow names
    # Extract unique elements from flow names
    element_symbols = []
    for flow_name in combined_is_df['flow name']:
        # Try to extract element symbol from flow name
        # This is a simple approach - can be enhanced
        if isinstance(flow_name, str):
            # Look for known element symbols
            known_elements = ['Al', 'Cr', 'Cu', 'Fe', 'Pb', 'Mn', 'Mo', 'Ni', 'U', 'Zn', 'P']
            for elem in known_elements:
                if elem in flow_name:
                    element_symbols.append(elem)
                    break
            else:
                element_symbols.append(None)
        else:
            element_symbols.append(None)
    
    combined_is_df['symbol'] = element_symbols
    
    # Step 4: Add molar masses
    M_list = []
    for index, row in combined_is_df.iterrows():
        if row['symbol']:
            try:
                M = element(row['symbol']).atomic_weight
            except:
                M = np.nan
        else:
            M = np.nan
        M_list.append(M)
    combined_is_df['M'] = M_list
    
    # Step 5: Calculate delta_bc or ERC
    def delta_bc(xi, dg):
        """Calculate change in concentration exergy."""
        R = 8.314
        T = 290.15
        return -R * T * (np.log(xi) + ((1 - xi) / xi) * np.log(1 - xi)) * dg
    
    if option == 'ERC':
        # Option 2: ERC calculation
        ERC_list = []
        for index, row in combined_is_df.iterrows():
            if pd.notna(row['Initial Concentration']) and pd.notna(row['OG decrease']) and pd.notna(row['k']):
                ERC = row['k'] * delta_bc(row['Initial Concentration'] / 100, row['OG decrease'] / 100)
                ERC_m = ERC / row['M'] if pd.notna(row['M']) else np.nan
                ERC_list.append(ERC_m)
            else:
                ERC_list.append(np.nan)
        combined_is_df['CF2_ERC'] = ERC_list
    else:
        # Option 1: bc calculation
        delta_bc_list = []
        for index, row in combined_is_df.iterrows():
            if pd.notna(row['Initial Concentration']) and pd.notna(row['OG decrease']):
                dbc = delta_bc(row['Initial Concentration'] / 100, row['OG decrease'] / 100)
                dbc_m = dbc / row['M'] if pd.notna(row['M']) else np.nan
                delta_bc_list.append(dbc_m)
            else:
                delta_bc_list.append(np.nan)
        combined_is_df['CF2_bc'] = delta_bc_list
    
    return combined_is_df


def create_method_dynamically(method_name_tuple, method_data, metadata=None):
    """
    Create or update a Brightway2 method dynamically.
    
    Args:
        method_name_tuple (tuple): Method name as tuple (category, name, subcategory)
        method_data (list): List of (flow_key, value) tuples
        metadata (dict): Method metadata
    
    Returns:
        bd.Method: The created/updated method object
    """
    # Default metadata
    if metadata is None:
        metadata = {}
    
    # Update dynamic fields
    num_elements = len(set(
        bd.get_activity(cf[0])['name'].split(',')[0].split()[0] 
        for cf in method_data 
        if isinstance(cf[0], tuple)
    )) if method_data else 0
    
    default_metadata = {
        'unit': 'KJ-Eq',
        'description': f'Impact analysis for ore grade decline potential',
        'version': '1.0',
        'num_cfs': len(method_data),
        'application': 'Input product-system metals characterization'
    }
    
    # Merge with provided metadata
    final_metadata = {**default_metadata, **metadata}
    
    # Update dynamic fields in metadata
    if 'Applied to' in method_name_tuple[2]:
        # Update the element count in the method name
        method_name_tuple = (
            method_name_tuple[0],
            method_name_tuple[1],
            f"Applied to {num_elements} elements"
        )
    
    final_metadata['num_cfs'] = len(method_data)
    
    # Create or update method
    method_object = bd.Method(method_name_tuple)
    
    try:
        method_object.register(**final_metadata)
        method_object.write(method_data)
        print(f"✅ Successfully created/updated method: {method_name_tuple}")
        print(f"   - Unit: {final_metadata['unit']}")
        print(f"   - Number of CFs: {len(method_data)}")
        print(f"   - Elements: {num_elements}")
        return method_object
    except Exception as e:
        print(f"❌ Failed to write method: {str(e)}")
        raise


def run_full_workflow(country='ES', voltage='high', option='ERC'):
    """
    Run the full automated workflow from LCA to characterization factors.
    
    Args:
        country (str): Country code
        voltage (str): Voltage level
        option (str): 'ERC' or 'bc'
    
    Returns:
        dict: Results containing LCA, inventory, elementary flows, and CFs
    """
    # Step 1: Run LCA
    lca, inventory, ef_df = run_lca_electricity(country, voltage)
    
    if lca is None:
        return None
    
    # Step 2: Load OGD constants
    try:
        ogd_df = pd.read_excel("Ore-GradeDeclineConstants.xlsx")
    except:
        print("Error loading Ore-GradeDeclineConstants.xlsx")
        return None
    
    # Step 3: Process elementary flows
    # Clean flow names
    ef_df['cleaned_name'] = ef_df['flow_name'].apply(lambda x: x.split(',')[0].strip() if isinstance(x, str) else x)
    
    # Filter for metal flows
    metal_keywords = ['aluminium', 'chromium', 'copper', 'iron', 'lead', 'manganese', 
                     'molybdenum', 'nickel', 'zinc', 'uranium', 'phosphorus']
    
    metal_flows = ef_df[ef_df['flow_name'].str.lower().str.contains('|'.join(metal_keywords))]
    
    # Create combined_IS_df from metal flows
    combined_is_df = pd.DataFrame({
        'flow name': metal_flows['cleaned_name'],
        'OG decrease': metal_flows['amount']  # Using amount as proxy for OG decrease
    })
    
    # Step 4: Calculate characterization factors
    result_df = calculate_characterization_factors(ogd_df, combined_is_df, option)
    
    # Step 5: Create method
    method_data = []
    for _, row in result_df.iterrows():
        if pd.notna(row.get('CF2_ERC')):
            # Find the flow key
            flow_key = metal_flows[metal_flows['cleaned_name'] == row['flow name']]['flow_key'].iloc[0]
            method_data.append((flow_key, row['CF2_ERC']))
        elif pd.notna(row.get('CF2_bc')):
            flow_key = metal_flows[metal_flows['cleaned_name'] == row['flow name']]['flow_key'].iloc[0]
            method_data.append((flow_key, row['CF2_bc']))
    
    # Create dynamic method name
    method_name_tuple = (
        "Future Effort method",
        f"{country} Electricity, {voltage} voltage",
        f"Surplus Exergy - {'ERC_dissipative' if option == 'ERC' else 'bc'}"
    )
    
    # Create method
    method_obj = create_method_dynamically(method_name_tuple, method_data)
    
    return {
        'lca': lca,
        'inventory': inventory,
        'elementary_flows': ef_df,
        'characterization_factors': result_df,
        'method': method_obj,
        'method_name': method_name_tuple
    }
