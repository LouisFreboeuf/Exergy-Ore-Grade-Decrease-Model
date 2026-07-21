# Data Directory

This directory contains processed data files for the Exergy Ore Grade Decrease Model.

## Files

- **PubChem_Info_EI34.csv**: Element information from PubChem for ecoinvent 3.4 biosphere flows
- **PubChem_CF2_Cu_Cathode_EI34.csv**: Characterization factors for copper cathode flows
- **PubChem_CF2_Cu_Cathode_NotFound_EI34.csv**: CF2 data for flows not found in PubChem
- **PubChem_Method_EI34.csv**: Method data for ecoinvent 3.4
- **PubChem_NotEmission_EI34.csv**: Non-emission flows from PubChem
- **PubChem_NotFound_EI34.csv**: Flows not found in PubChem

## Data Sources

- **ecoinvent 3.4**: Life cycle inventory database
- **PubChem**: Chemical information from NCBI

## Notes

- All CSV files have been deduplicated to remove redundant rows
- Files use comma-separated format with quoted strings
- First row contains column headers
