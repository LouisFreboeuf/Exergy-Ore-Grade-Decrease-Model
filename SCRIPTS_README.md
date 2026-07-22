# Automated OGD Calculation Scripts

This directory contains Python scripts for automating the Ore Grade Decline (OGD) calculations using Brightway25.

## Scripts Available

### 1. `direct_ogd_calculation.py` (Recommended)

This script does exactly what you requested:

1. **Imports data** from `Results/EsElec/EsS1.csv`
2. **Creates the LCIA method** with your exact metadata specification
3. **Builds the functional unit** for 268 TWh of electricity production from high voltage Spain electricity main market
4. **Calculates elementary flow contributions** automatically

#### Usage:
```bash
python direct_ogd_calculation.py
```

#### What it does:
- Loads the existing EsS1.csv results
- Creates the "Cumulative Ore Grade Decline" method with your metadata
- Finds the Spanish high voltage electricity activity
- Creates a functional unit of 268 TWh
- Calculates and saves the elementary flow contributions
- Outputs results in the same format as EsS1.csv

### 2. `automated_ogd_calculation.py`

A more comprehensive version that includes additional verification and error handling.

### 3. `calculate_ogd_brightway.py`

A full workflow script that also includes the CF1 calculation from the Excel file.

## Requirements

- Brightway25 (`bw2data`, `bw2calc`, `bw2io`)
- Pandas
- NumPy
- Ecoinvent 3.4 databases (cutoff and biosphere)

## Setup

1. Make sure you have the ecoinvent databases imported in Brightway25
2. Set your project to "SurplusEx" or modify the script
3. Ensure the `Results/EsElec/EsS1.csv` file exists

## Expected Output

The scripts will create:

1. **LCIA Method**: "Cumulative Ore Grade Decline" with your specified metadata
2. **Functional Unit**: 268 TWh of Spanish high voltage electricity
3. **Results Files**:
   - `Results/EsElec/EsS1_direct_calculation.csv` - Elementary flow contributions
   - `Results/EsElec/EsS1_automated_direct.csv` - Results in EsS1 format

## Method Metadata Used

The scripts use your exact metadata specification:

```python
method_name_tuple = (
    "Cumulative Ore Grade Decline",
    "Cumulative ore grade variation",
    f"Applied to {len(method_data)} elements"
)

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
```

## Notes

- The scripts automatically handle unit conversion for the functional unit
- They search for the most appropriate Spanish electricity activity
- Results are saved in multiple formats for compatibility
- Error handling is included for missing data or activities