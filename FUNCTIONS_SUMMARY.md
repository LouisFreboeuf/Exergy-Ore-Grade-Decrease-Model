# OGD Functions Summary

I've created **reusable functions** that you can **import and use directly in your notebook**. These functions address all your requirements:

## Key Features

✅ **No CSV files used** - Results come directly from `bw2calc`  
✅ **Method name uses element count** - `f"Applied to {len(OGD_df)} elements"`  
✅ **Functional unit for 268 TWh** - Spanish high voltage electricity  
✅ **Elementary flow contributions** - Calculated directly via `bw2calc`  

## Functions Available

### 1. Core Functions (from `ogd_functions.py`)

#### `create_ogd_method_from_dataframe(OGD_df, method_name_suffix=None)`
```python
# Creates the OGD method from your DataFrame
method_object, method_data = create_ogd_method_from_dataframe(OGD_df)
```
- **Input**: OGD_df (your ore grade decline data)
- **Output**: method_object, method_data
- **Method name**: Uses **element count** from OGD_df, not CF count
- **Metadata**: Uses your exact specification

#### `find_spanish_electricity_activity()`
```python
# Finds Spanish high voltage electricity activities
electricity_activities = find_spanish_electricity_activity()
electricity_activity = electricity_activities[0]  # Use first match
```

#### `create_functional_unit(electricity_activity, amount_twh=268)`
```python
# Creates functional unit for 268 TWh
fu, amount, unit_display = create_functional_unit(electricity_activity, amount_twh=268)
```
- **Input**: electricity activity and amount in TWh (default: 268)
- **Output**: functional unit dictionary, converted amount, unit display string
- **Automatic unit conversion**: Handles kWh, MJ, GJ

#### `calculate_lcia_with_bw2calc(fu, method_name_tuple)`
```python
# Calculates LCIA directly using bw2calc (NO CSV FILES!)
results = calculate_lcia_with_bw2calc(fu, method_name_tuple)
```
- **Input**: functional unit, method name tuple
- **Output**: Dictionary with total_score, elementary_contributions DataFrame, and LCA object
- **Elementary contributions**: Directly from `lca.characterized_inventory`

#### Helper functions
```python
# Get formatted top/bottom contributions
get_top_contributions(elementary_contributions, n=10)
get_bottom_contributions(elementary_contributions, n=10)
```

### 2. Complete Workflow Function

#### `run_complete_workflow(OGD_df_path='Ore-GradeDeclineConstants.xlsx', amount_twh=268)`
```python
# Does everything automatically
results = run_complete_workflow(amount_twh=268)
```
- Loads OGD data
- Creates method
- Finds electricity activity
- Creates functional unit
- Calculates LCIA
- Returns complete results

## Usage in Your Notebook

### Simple Usage (Recommended)

```python
# Import the functions
from ogd_functions import (
    create_ogd_method_from_dataframe,
    find_spanish_electricity_activity,
    create_functional_unit,
    calculate_lcia_with_bw2calc
)

# Set up Brightway
import bw2data as bd
bd.projects.set_current("SurplusEx")

# Load your data
import pandas as pd
OGD_df = pd.read_excel('Ore-GradeDeclineConstants.xlsx')

# Create method (uses ELEMENT count, not CF count)
method_object, method_data = create_ogd_method_from_dataframe(OGD_df)

# Find Spanish electricity
activities = find_spanish_electricity_activity()
electricity_activity = activities[0]

# Create functional unit for 268 TWh
fu, amount, unit = create_functional_unit(electricity_activity, amount_twh=268)

# Calculate LCIA directly with bw2calc
results = calculate_lcia_with_bw2calc(fu, method_object.name)

# Access results
total_score = results['total_score']
elementary_contributions = results['elementary_contributions']
lca = results['lca']

# View top contributions
print(elementary_contributions.head(10))
```

### Even Simpler - Complete Workflow

```python
from ogd_functions import run_complete_workflow

# Run everything automatically
results = run_complete_workflow(amount_twh=268)

# Access results
print(f"Total score: {results['total_score']}")
print(results['elementary_contributions'].head(10))
```

## Method Name Correction

As you requested, the method name now correctly uses the **number of elements** from `OGD_df`, not the number of characterization factors:

```python
# In create_ogd_method_from_dataframe():
num_elements = len(OGD_df)  # Number of elements (metals)
method_name_tuple = (
    "Cumulative Ore Grade Decline",
    "Cumulative ore grade variation",
    f"Applied to {num_elements} elements"  # ✅ Uses ELEMENT count
)

# But num_cfs in metadata uses the actual CF count:
method_metadata = {
    'num_cfs': len(method_data),  # ✅ This is the CF count
    # ... other metadata
}
```

## Results Format

The `calculate_lcia_with_bw2calc()` function returns:

```python
{
    'total_score': float,           # Total LCIA score
    'elementary_contributions': DataFrame,  # All elementary flow contributions
    'lca': LCA object               # The LCA object for further analysis
}
```

The `elementary_contributions` DataFrame contains:
- `flow_key`: Brightway flow key
- `flow_name`: Flow name
- `categories`: Flow categories
- `type`: Flow type
- `unit`: Flow unit
- `database`: Database name
- `contribution`: Contribution value
- `abs_contribution`: Absolute contribution (for sorting)

## Files Created

1. **`ogd_functions.py`** - All the reusable functions
2. **`example_usage.py`** - Example of how to use the functions
3. **`FUNCTIONS_SUMMARY.md`** - This summary

## Integration with Your Notebook

You can:

1. **Copy the functions** directly into your notebook cells
2. **Import the module**: `from ogd_functions import *`
3. **Use the complete workflow**: `run_complete_workflow()`

The functions are designed to work seamlessly with your existing notebook structure and use your exact metadata specification.