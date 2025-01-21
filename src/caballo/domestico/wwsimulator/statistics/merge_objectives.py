#!/usr/bin/env python

import os
import re
import pandas as pd
import sys

# Function to extract objective name from the file name
def extract_objective(file_name):
    try:
        return file_name.split(".")[0]
    except IndexError:
        raise ValueError(f"Could not extract objective name from file name: {file_name}")

# Function to merge two CSV files and add an objective column
def merge_objective_files(files, output_file):
    
    merged_df = None
    
    for file in files:
    
        # Extract objective names
        objective = extract_objective(os.path.basename(file))

        # Read the CSV files
        df = pd.read_csv(file)

        # Add the objective column
        df['objective'] = objective

        # Combine the dataframes
        if merged_df is None:
            merged_df = df
        else:
            merged_df = pd.concat([merged_df, df], ignore_index=True)

    # Save to the output CSV file
    merged_df.to_csv(output_file, index=False)
    print(f"Merged file saved to {output_file}")

# Example usage
if __name__ == "__main__":

    files = [arg for arg in sys.argv[1:-1]]
    output_file = sys.argv[-1]
    merge_objective_files(files, output_file)