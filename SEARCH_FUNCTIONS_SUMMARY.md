# Brightway25 Search Functions Summary

I've created **generic activity search functions** that you can **import and use directly in your notebook**. These address your requirements:

## ✅ **Requirements Addressed**

1. **Fixed JSON error** - Created script to fix f-string double quotes in notebook
2. **Generic activity search function** - `search_activities(name, location, database, reference_product)`
3. **Specific Spanish electricity finder** - `find_spanish_electricity()`
4. **Inventory flows from bw2calc** - `get_inventory_flows(fu_dict, method)`
5. **Elementary flow contributions** - `get_elementary_flow_contributions(fu_dict, method_name_tuple)`

## 📋 **Main Functions**

### 1. **`search_activities(name=None, location=None, database=None, reference_product=None, limit=10)`**

**Generic function to search for activities by name and location:**

```python
from brightway_utils import search_activities

# Search for electricity activities in Spain
activities = search_activities(name='electricity', location='spain', limit=5)

# Search for copper activities in Chile
copper_activities = search_activities(name='copper', location='chile')

# Search in specific database
cutoff_activities = search_activities(name='steel', database='ecoinvent-3.4-cutoff')
```

**Parameters:**
- `name`: Activity name (case insensitive, partial match)
- `location`: Location filter (case insensitive, partial match)
- `database`: Database to search in
- `reference_product`: Reference product filter
- `limit`: Maximum results to return

**Returns:** List of matching activities

### 2. **`find_spanish_electricity()`**

**Find Spanish high voltage electricity activities:**

```python
from brightway_utils import find_spanish_electricity

# Find Spanish electricity activities
spanish_activities = find_spanish_electricity()

# Use the first match
electricity_activity = spanish_activities[0]
```

**Returns:** List of Spanish electricity activities (prioritizing high voltage main market)

### 3. **`get_activity_by_name_and_location(name, location, database=None)`**

**Get specific activity by name and location:**

```python
from brightway_utils import get_activity_by_name_and_location

# Get specific activity
activity = get_activity_by_name_and_location(
    name='electricity, high voltage, main market',
    location='ES'
)
```

**Returns:** Single activity or None

### 4. **`get_inventory_flows(fu_dict, method=None)`**

**Get inventory flows using bw2calc (inspired by your provided code):**

```python
from brightway_utils import get_inventory_flows, create_functional_unit

# Create functional unit
fu = create_functional_unit(electricity_activity, amount=268 * 10**9)

# Get inventory flows
inventory_df = get_inventory_flows(fu)

# View results
print(inventory_df.head(10)[['Flow Name', 'Amount', 'Unit']])
```

**Returns:** DataFrame with inventory flows and amounts

### 5. **`get_elementary_flow_contributions(fu_dict, method_name_tuple)`**

**Get elementary flow contributions using bw2calc:**

```python
from brightway_utils import get_elementary_flow_contributions

# Get contributions
contributions_df, total_score = get_elementary_flow_contributions(fu, method_name_tuple)

# View top contributions
print(f"Total score: {total_score}")
print(contributions_df.head(10)[['Flow Name', 'Contribution']])
```

**Returns:** DataFrame with contributions, total score

### 6. **`create_functional_unit(activity, amount, unit=None)`**

**Create functional unit with automatic unit conversion:**

```python
from brightway_utils import create_functional_unit

# Create functional unit for 268 TWh
fu = create_functional_unit(electricity_activity, amount=268 * 10**9)
```

**Parameters:**
- `activity`: Brightway25 activity
- `amount`: Amount for functional unit
- `unit`: Target unit (optional, converts automatically)

**Returns:** Functional unit dictionary

## 🚀 **Usage Examples**

### Example 1: Basic Activity Search

```python
from brightway_utils import search_activities

# Search for activities
activities = search_activities(
    name='electricity',
    location='spain',
    database='ecoinvent-3.4-cutoff',
    limit=5
)

for i, act in enumerate(activities):
    print(f"{i+1}. {act.get('name')} - {act.get('location')} - {act.get('reference product')}")
```

### Example 2: Complete LCA Workflow

```python
import bw2data as bd
from brightway_utils import (
    find_spanish_electricity, 
    create_functional_unit, 
    get_elementary_flow_contributions
)

# Set up project
bd.projects.set_current("SurplusEx")

# Find Spanish electricity
spanish_activities = find_spanish_electricity()
electricity_activity = spanish_activities[0]

# Create functional unit for 268 TWh
fu = create_functional_unit(electricity_activity, amount=268 * 10**9)

# Assuming you have a method created
method_name_tuple = ('Cumulative Ore Grade Decline', 'Cumulative ore grade variation', 'Applied to 17 elements')

# Get elementary flow contributions
contributions_df, total_score = get_elementary_flow_contributions(fu, method_name_tuple)

print(f"Total LCIA Score: {total_score}")
print("Top 10 contributions:")
print(contributions_df.head(10)[['Flow Name', 'Contribution']])
```

### Example 3: Inventory Analysis

```python
from brightway_utils import get_inventory_flows

# Get inventory flows
inventory_df = get_inventory_flows(fu)

# Analyze inventory
print(f"Total inventory flows: {len(inventory_df)}")
print("Top 5 flows by amount:")
print(inventory_df.head()[['Flow Name', 'Amount', 'Unit']])

# Filter by flow type
resource_flows = inventory_df[inventory_df['Type'] == 'natural resource']
print(f"Resource flows: {len(resource_flows)}")
```

## 📁 **Files Created**

1. **`brightway_utils.py`** - All search and utility functions
2. **`fix_notebook_json.py`** - Script to fix JSON issues in notebook
3. **`SEARCH_FUNCTIONS_SUMMARY.md`** - This summary

## 🔧 **JSON Fix**

The notebook has f-strings with double quotes that cause JSON parsing errors:

```python
# ❌ Problematic (causes JSON error):
method_name_tuple = (
    "Cumulative Ore Grade Decline",
    "Cumulative ore grade variation",
    f"Applied to {number of elements} elements"  # Double quotes issue
)

# ✅ Fixed (use single quotes):
method_name_tuple = (
    "Cumulative Ore Grade Decline",
    "Cumulative ore grade variation",
    f'Applied to {number of elements} elements'  # Single quotes work
)
```

Run `fix_notebook_json.py` to automatically fix these issues:

```bash
python fix_notebook_json.py
```

## 🎯 **Key Benefits**

1. **Generic search** - Works for any activity name and location
2. **Flexible filtering** - Filter by name, location, database, reference product
3. **bw2calc integration** - Uses bw2calc directly, no CSV files
4. **Automatic unit conversion** - Handles kWh, MJ, GJ conversions
5. **Error handling** - Robust error handling for missing data
6. **JSON compatible** - Fixed f-string issues for notebook compatibility

## 📖 **Integration with Your Notebook**

You can:

1. **Import functions directly:**
   ```python
   from brightway_utils import search_activities, find_spanish_electricity, get_elementary_flow_contributions
   ```

2. **Copy functions into notebook cells** - Copy the function definitions directly

3. **Use the complete workflow** - Import and use the functions as shown in examples

The functions are designed to work seamlessly with your existing notebook structure and use the same data structures as your provided example code.