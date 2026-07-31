#!/bin/bash

# Script to execute SurplusEx.ipynb for all 8 configurations defined in the workflow
# Uses local Python environment with Brightway

# Change to the script directory
cd "$(dirname "$0")"

# Define the configurations
configs=(
    "all_vieira_natural_resources::inputs/sop-vieira-constants_all.csv::inputs/sop-vieira-constants_all.csv::natural_resource"
    "all_vieira_dissipation::inputs/sop-vieira-constants_all.csv::inputs/sop-vieira-constants_all.csv::dissipation"
    "all_valero_natural::inputs/sop-vieira-constants_all.csv::inputs/valero-constants_with_xm.csv::natural_resource"
    "all_valero_dissipation::inputs/sop-vieira-constants_all.csv::inputs/valero-constants_with_xm.csv::dissipation"
    "updatedFe_vieira_natural_resources::inputs/sop-vieira-constants_updatedFe.csv::inputs/sop-vieira-constants_updatedFe.csv::natural_resource"
    "updatedFe_vieira_dissipation::inputs/sop-vieira-constants_updatedFe.csv::inputs/sop-vieira-constants_updatedFe.csv::dissipation"
    "updatedFe_valero_natural::inputs/sop-vieira-constants_updatedFe.csv::inputs/valero-constants_with_xm.csv::natural_resource"
    "updatedFe_valero_dissipation::inputs/sop-vieira-constants_updatedFe.csv::inputs/valero-constants_with_xm.csv::dissipation"
)

# Create results directory if it doesn't exist
mkdir -p results

echo "Starting SurplusEx.ipynb execution for all configurations..."
echo "Results will be saved in the results/ directory."
echo ""

# Loop through all configurations
for config in "${configs[@]}"; do
    # Split the configuration into parts
    IFS='::' read -r -a parts <<< "$config"
    config_name="${parts[0]}"
    viera_csv_input_data="${parts[1]}"
    input_for_xi="${parts[2]}"
    focus="${parts[3]}"

    echo "=========================================="
    echo "Processing configuration: $config_name"
    echo "  viera_csv_input_data: $viera_csv_input_data"
    echo "  input_for_xi: $input_for_xi"
    echo "  focus: $focus"
    echo "=========================================="

    # Run the notebook with the current configuration
    echo "Executing notebook..."
    jupyter nbconvert --to notebook --execute SurplusEx.ipynb \
        --output "results/SurplusEx_${config_name}.ipynb" \
        --ExecutePreprocessor.timeout=1800 \
        --ExecutePreprocessor.allow_errors=False \
        --var viera_csv_input_data="$viera_csv_input_data" \
        --var input_for_xi="$input_for_xi" \
        --var focus="$focus"

    # Check if execution was successful
    if [ $? -eq 0 ]; then
        echo "Notebook executed successfully for $config_name"
        
        # Move all_results.json to results directory with config suffix
        if [ -f "all_results.json" ]; then
            mv "all_results.json" "results/all_results_${config_name}.json"
            echo "Moved all_results.json to results/all_results_${config_name}.json"
        else
            echo "Warning: all_results.json not found after execution"
        fi
    else
        echo "Error: Notebook execution failed for $config_name"
        exit 1
    fi

    echo ""
done

echo "All configurations processed successfully!"
echo "Results saved in results/ directory."
