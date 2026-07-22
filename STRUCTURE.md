# Clean Project Structure

## 📁 **Current Structure**

```
Exergy-Ore-Grade-Decrease-Model/
├── OGD_LCA_Workflow.ipynb          # Main executable notebook
├── SurplusEx.ipynb                 # Original notebook (unchanged)
├── clean.py                       # Existing file
├── validate_data.py               # Existing file
├── src/                          # Functions package
│   ├── __init__.py               # Package initialization
│   ├── brightway_utils.py        # Activity search functions
│   └── ogd_functions.py          # OGD calculation functions
└── .git/                         # Git repository
```

## 🎯 **What You Requested**

✅ **Clean structure** - Functions in `src/`, notebook calls functions  
✅ **Single notebook** - `OGD_LCA_Workflow.ipynb` with executable cells  
✅ **Examples as cells** - Each major step has its own cell  
✅ **No mess** - Removed all redundant scripts and files  

## 📖 **How to Use**

### 1. **Run the Notebook**

Open `OGD_LCA_Workflow.ipynb` in VS Code or Jupyter. The notebook has:

- **Cell 1-2**: Setup and imports from `src/`
- **Cell 3-4**: Brightway25 setup
- **Cell 5-6**: Load OGD data
- **Cell 7-8**: Search for activities by name and location
- **Cell 9-10**: Create OGD method
- **Cell 11-12**: Create functional unit for 268 TWh
- **Cell 13-14**: Calculate LCIA and get elementary flow contributions
- **Cell 15-16**: Get inventory flows (optional)
- **Cell 17-18**: Complete workflow (alternative)

### 2. **Import Functions in Your Code**

```python
# Import from src package
from src import (
    search_activities,
    find_spanish_electricity,
    create_ogd_method_from_dataframe,
    create_functional_unit,
    calculate_lcia_with_bw2calc,
    get_inventory_flows,
    get_elementary_flow_contributions
)

# Use the functions
activities = search_activities(name='electricity', location='spain')
method_object, method_data = create_ogd_method_from_dataframe(OGD_df)
fu, amount, unit = create_functional_unit(activity, amount_twh=268)
results = calculate_lcia_with_bw2calc(fu, method_name_tuple)
```

## 🔧 **Functions Available**

### In `src/brightway_utils.py`:

- `search_activities(name, location, database, reference_product)` - **Generic activity search**
- `find_spanish_electricity()` - Find Spanish high voltage electricity
- `get_activity_by_name_and_location(name, location)` - Get specific activity
- `get_inventory_flows(fu_dict)` - Get inventory flows using bw2calc
- `get_elementary_flow_contributions(fu_dict, method)` - Get elementary flow contributions
- `create_functional_unit(activity, amount, unit)` - Create functional unit

### In `src/ogd_functions.py`:

- `clean_chemical_name(name)` - Clean chemical names
- `chem_comp(mf)` - Parse molecular formulas
- `has_elem(parts, dict)` - Check element presence
- `cf_calculator(dict, mw, parts)` - Calculate characterization factors
- `create_ogd_method_from_dataframe(OGD_df)` - Create OGD method
- `run_complete_workflow(OGD_df_path, amount_twh)` - Complete workflow

## 🚀 **Key Features**

1. **Clean separation**: Functions in `src/`, notebook for demonstration
2. **Executable cells**: Each step in the notebook can be run independently
3. **Clear documentation**: Each cell has comments explaining what it does
4. **Error handling**: Functions include proper error handling
5. **bw2calc integration**: All calculations use bw2calc directly (no CSV files)

## 📝 **Notebook Structure**

The `OGD_LCA_Workflow.ipynb` notebook follows this flow:

```
1. Setup and Imports
   └── Import all functions from src/

2. Brightway25 Setup
   └── Set up project and check databases

3. Load Ore Grade Decline Data
   └── Load from Ore-GradeDeclineConstants.xlsx

4. Search for Activities
   ├── Generic activity search example
   └── Find Spanish electricity example

5. Create OGD Method
   └── Create method from OGD dataframe

6. Create Functional Unit
   └── 268 TWh of Spanish electricity

7. Calculate LCIA
   └── Get elementary flow contributions

8. Get Inventory Flows (Optional)
   └── Get inventory flows using bw2calc

9. Complete Workflow (Alternative)
   └── Run everything with one function call

10. Summary
    └── Documentation of all functions and workflow
```

## 🔗 **Pull Request**

The clean structure is available in the pull request:
- **Branch**: `vibe/lca-automation-32e990`
- **URL**: https://github.com/LouisFreboeuf/Exergy-Ore-Grade-Decrease-Model/pull/2

## ✅ **Requirements Met**

1. ✅ **Re-optimized branch** - Clean structure with proper organization
2. ✅ **Examples as notebook cells** - `OGD_LCA_Workflow.ipynb` with executable cells
3. ✅ **Functions in src/** - All functions moved to `src/` directory
4. ✅ **Notebook calls functions** - Single notebook that imports and uses functions from `src/`
5. ✅ **No mess** - Removed all redundant and unnecessary files

You can now run the notebook cells step-by-step to understand the structure and test the functions!