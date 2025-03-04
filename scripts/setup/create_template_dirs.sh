#!/bin/bash

# Base template directory
mkdir -p src/reading_list/templates/{email,excel,reports,tbr,styles}

# Report-specific directories
mkdir -p src/reading_list/templates/reports/{chain,projected,yearly}

# Move files
mv templates/email/* src/reading_list/templates/email/
mv templates/excel/* src/reading_list/templates/excel/
mv templates/reports/styles/* src/reading_list/templates/styles/
mv templates/reading_chain.html src/reading_list/templates/reports/chain/
mv templates/reports/reading_chain_report.html src/reading_list/templates/reports/chain/
mv templates/reports/projected_* src/reading_list/templates/reports/projected/
mv templates/reports/yearly_reading_report.html src/reading_list/templates/reports/yearly/
mv templates/tbr/* src/reading_list/templates/tbr/

# Update paths in Python files
find src/reading_list -type f -name "*.py" -exec sed -i 's|templates/email|src/reading_list/templates/email|g' {} +
find src/reading_list -type f -name "*.py" -exec sed -i 's|templates/excel|src/reading_list/templates/excel|g' {} +
find src/reading_list -type f -name "*.py" -exec sed -i 's|templates/reports|src/reading_list/templates/reports|g' {} +