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
def merge_objective_files(file1, file2, output_file):
    # Extract objective names
    objective1 = extract_objective(os.path.basename(file1))
    objective2 = extract_objective(os.path.basename(file2))

    # Read the CSV files
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)

    # Add the objective column
    df1['objective'] = objective1
    df2['objective'] = objective2

    # Combine the dataframes
    merged_df = pd.concat([df1, df2], ignore_index=True)

    # Save to the output CSV file
    merged_df.to_csv(output_file, index=False)
    print(f"Merged file saved to {output_file}")

# Example usage
if __name__ == "__main__":

    file1 = sys.argv[1]
    file2 = sys.argv[2]
    output_file = sys.argv[3]
    merge_objective_files(file1, file2, output_file)