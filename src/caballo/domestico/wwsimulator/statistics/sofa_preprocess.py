#!/usr/bin/env python

# Use this module to transform each simulation run output into a dataset
# digestible by SOFA.

import os
import pandas as pd

# Function to extract lambda value from the file name
def extract_lambda(file_name):
    try:
        parts = file_name.split("_lambda=")
        lambda_value = parts[1].split("_")[0]
        return float(lambda_value)
    except (IndexError, ValueError):
        raise ValueError(f"Could not extract lambda value from file name: {file_name}")

def extract_seed(file_name):
    try:
        seed = file_name.split("_")[-1].split(".")[0]
        return int(seed)
    except (IndexError, ValueError):
        raise ValueError(f"Could not extract seed value from file name: {file_name}")

def get_csv_simple_names(input_folder):
    all_files = [f for f in os.listdir(input_folder) if f.endswith('.csv')]
    return all_files

# Function to process and merge CSV files
def merge_csv_files(input_folder, output_file):
    all_files = [f for f in os.listdir(input_folder) if f.endswith('.csv')]
    merged_data = []

    for file in all_files:
        file_path = os.path.join(input_folder, file)
        lambda_value = extract_lambda(file)
        seed = extract_seed(file)

        # Read the CSV file
        df = pd.read_csv(file_path)

        # Add lambda column
        df['lambda'] = lambda_value

        # Split the statistic column into node, metric, and aggregation
        statistic_split = df['statistic'].str.split('-', expand=True)
        df['node'] = statistic_split[0]
        df['metric'] = statistic_split[1]
        df['aggregation'] = statistic_split[2]
        df['seed'] = seed

        # Drop the old statistic column
        df = df.drop(columns=['statistic'])

        merged_data.append(df)

    # Combine all dataframes
    final_df = pd.concat(merged_data, ignore_index=True)

    # Save to the output CSV file
    final_df.to_csv(output_file, index=False)
    print(f"Merged file saved to {output_file}")

# Example usage
if __name__ == "__main__":
    objectives = ["1", "2", "3", "4_04", "4_045", "4_05", "4_055", "4_06", "4_065", "4_07", "4_075", "4_08"]
    simulations = ["BatchMeansSimulation", "ReplicatedSimulation", "TransientSimulation"]
    for obj in objectives:
        for sim in simulations:
            input_folder = os.path.join(".", f"objective_{obj}", f"{sim}")
            output_file = f"objective_{obj}_{sim}.csv"
            try:
                merge_csv_files(input_folder, output_file)
            except FileNotFoundError as e:
                print(f"Skipping objective_{obj}_{sim}: {e}")
                continue