# Code Replacements for SurplusEx.ipynb

This document provides the exact code replacements to automate your notebook workflow.

---

## Replacement 1: CSV Import → LCA Automation

### Original Code (Cell 17)
```python
# Import data 
IS1_df = pd.read_csv('Results/EsElec/EsS1.csv')
IS1_df.head(3)
```

### Replacement Code
```python
# Run LCA for high-voltage electricity in Spain
from src.lca_automation import run_lca_electricity, get_elementary_flow_contributions

lca_es, inventory_es, ef_df_es = run_lca_electricity(country='ES', voltage='high')

# Filter for metal flows and create IS1_df equivalent
metal_keywords = ['aluminium', 'chromium', 'copper', 'iron', 'lead', 'manganese', 
                 'molybdenum', 'nickel', 'zinc', 'uranium', 'phosphorus']

metal_flows_es = ef_df_es[ef_df_es['flow_name'].str.lower().str.contains('|'.join(metal_keywords))]

IS1_df = pd.DataFrame({
    'flow name': metal_flows_es['flow_name'],
    'OG decrease': metal_flows_es['amount']
})

# Clean flow names
IS1_df['flow name'] = IS1_df['flow name'].apply(
    lambda x: x.split(',')[0].strip() if isinstance(x, str) else x
)

IS1_df.head(3)
```

---

## Replacement 2: Manual Calculation Steps → Automated Function

### Original Code (Cell 28)
```python
# Step 1: Calculates the initial concentration of each mine and add it to OGD_df 
xi_list = []
for index,row in OGD_df.iterrows():
    xi = OG_ini(row['alpha'],row['beta'],row['URR'],row['CME'])
    xi_list.append(xi)
OGD_df['Initial Concentration'] = xi_list

# Step 2: For the rows in combined_IS_df that matches the element in OGD_df, add its xi
for index,row in combined_IS_df.iterrows():
    xi = OGD_df[OGD_df['Metal']==row['flow name']]['Initial Concentration']

    combined_IS_df.at[index,'Initial Concentration'] = xi.iloc[0] # the .iloc[0] is to convert xi from a Series to a float that can be easily read by pandas

# Step 3: For the rows in combined_IS_df that matches the element in OGD_df, add its k
for index,row in combined_IS_df.iterrows():
    xi = OGD_df[OGD_df['Metal']==row['flow name']]['k']
    combined_IS_df.at[index,'k'] = xi.iloc[0] # the .iloc[0] is to convert k from a Series to a float that can be easily read by pandas

# Step 3: Add the symbols to the DataFrame
Cu_list = ['Al','Cr','Cu','Fe','Pb','Mo','Ni','Zn']
Fr_elem_list = ['Al','Cr','Cu','Fe','Pb','Mn','Mo','Ni','U','Zn']
Es_elem_list = ['Al','Cr','Cu','Fe','Pb','Mn','Mo','Ni','P','U','Zn']
combined_IS_df['symbol'] = Es_elem_list

# Step 4: Add the molar mass of each element correspondingly
M_list = []
for index,row in combined_IS_df.iterrows():
    M = element(row['symbol']).atomic_weight
    M_list.append(M)
combined_IS_df['M'] = M_list

## Option 1
# Step 5: Compute for the delta_bc value 
delta_bc_list = []
for index,row in combined_IS_df.iterrows():
    dbc = Delta_bc(row['Initial Concentration']/100,row['OG decrease']/100)
    dbc_m = dbc/row['M']
    delta_bc_list.append(dbc_m)
combined_IS_df['CF2_bc'] = delta_bc_list

## Option 2
# Step 5: Compute for the delta_bc value 
ERC_list = []
for index,row in combined_IS_df.iterrows():
    ERC = row['k']*Delta_bc(row['Initial Concentration']/100,row['OG decrease']/100)
    ERC_m = ERC/row['M']
    ERC_list.append(ERC_m)
combined_IS_df['CF2_ERC'] = ERC_list

combined_IS_df
```

### Replacement Code
```python
# Use automated characterization factor calculation
from src.lca_automation import calculate_characterization_factors

# Calculate CFs with ERC option (or 'bc' for Option 1)
combined_IS_df = calculate_characterization_factors(
    OGD_df, 
    combined_IS_df, 
    option='ERC'  # or 'bc' for Option 1
)

combined_IS_df
```

---

## Replacement 3: Static Method Definition → Dynamic Method Creation

### Original Code (Cell 38 - French Electricity)
```python
# 1. Define the method name as a tuple for the desired hierarchy
method_name_tuple = (
   "Future Effort method",
    "French Electricity per capita", #Update system name
    "Surplus Exergy - ERC_dissipative"  # Updated name
)

# 2. Define metadata for the method, including the unit and a description
method_metadata = {
    'unit': 'KJ-Eq',
    'description': 'impact analysis specifically for 1545 kWh of electricity produced in France',
    'source': 'The values are taken from the appendix of ReCiPe 2016: https://www.rivm.nl/bibliotheek/rapporten/2016-0104.pdf',
    'version': '1.0', #I can try to update this number
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
```

### Replacement Code
```python
# Dynamic method creation
from src.lca_automation import create_method_dynamically

# Count actual elements with valid CFs
num_elements = len(combined_IS_df[pd.notna(combined_IS_df['CF2_ERC'])])

# Dynamic method name
method_name_tuple = (
    "Future Effort method",
    "French Electricity, high voltage",  # Dynamic based on LCA parameters
    f"Surplus Exergy - ERC_dissipative ({num_elements} elements)"  # Dynamic count
)

# Dynamic metadata
method_metadata = {
    'unit': 'KJ-Eq',
    'description': f'Impact analysis for ore grade decline potential - {num_elements} elements',
    'source': 'The values are taken from the appendix of ReCiPe 2016: https://www.rivm.nl/bibliotheek/rapporten/2016-0104.pdf',
    'version': '1.0',
    'num_cfs': len(method_data),
    'application': 'Input product-system metals characterization'
}

# Create method dynamically
method_object = create_method_dynamically(
    method_name_tuple, 
    method_data, 
    method_metadata
)
```

---

## Replacement 4: Ore-Grade Decline Method (Cell 14)

### Original Code
```python
# 1. Define the method name as a tuple for the desired hierarchy
method_name_tuple = (
    "Future Effort method",
    "Ore-Grade Decline Potential",
    "Applied to 17 elements"  # Updated name
)

# 2. Define metadata for the method, including the unit and a description
method_metadata = {
    'unit': 'change in ore grade per kg of metal extracted',
    'description': 'This LCIA method is one out of the 3 steps of the currently developing surplus exergy method. It models the...',
    'version': '1.0',
    'num_cfs': len(method_data),
    'application': 'Input product-system metals characterization'
}
```

### Replacement Code
```python
# Dynamic method name based on actual element count
num_elements = len(OGD_df)  # or count from your actual data

method_name_tuple = (
    "Future Effort method",
    "Ore-Grade Decline Potential",
    f"Applied to {num_elements} elements"  # Dynamic count
)

method_metadata = {
    'unit': 'change in ore grade per kg of metal extracted',
    'description': 'This LCIA method is one out of the 3 steps of the currently developing surplus exergy method. It models the ore grade decline potential.',
    'version': '1.0',
    'num_cfs': len(method_data),
    'application': 'Input product-system metals characterization'
}
```

---

## Full Workflow Example

For a complete automated workflow, you can use:

```python
from src.lca_automation import run_full_workflow

# Run everything for Spain, high voltage, ERC option
results = run_full_workflow(
    country='ES', 
    voltage='high', 
    option='ERC'
)

# Access results
lca = results['lca']
inventory = results['inventory']
elementary_flows = results['elementary_flows']
characterization_factors = results['characterization_factors']
method = results['method']
method_name = results['method_name']
```

---

## Setup Instructions

1. **Create the `src` directory** (already done)
2. **Copy `lca_automation.py`** to `src/` (already done)
3. **Add to imports** at the top of your notebook:
   ```python
   import sys
   sys.path.insert(0, 'src')
   from lca_automation import (
       run_lca_electricity,
       get_elementary_flow_contributions,
       calculate_characterization_factors,
       create_method_dynamically,
       run_full_workflow
   )
   ```

4. **Replace the cells** as shown above

---

## Benefits

- ✅ **No dependency on pre-calculated CSV files**
- ✅ **Reproducible results** - runs LCA fresh each time
- ✅ **Flexible** - works for any country/voltage
- ✅ **Maintainable** - cleaner, modular code
- ✅ **Dynamic** - method names and metadata update automatically
- ✅ **Scalable** - easy to extend to new scenarios
