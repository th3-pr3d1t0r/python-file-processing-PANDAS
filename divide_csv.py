import pandas as pd
import numpy as np
import os

def divide_csv_file(input_filename, output_names):
    """
    Divides a CSV file into ten approximately equal parts and saves them
    with specified names.

    Args:
        input_filename (str): The path to the input CSV file.
        output_names (list): A list of 10 strings for the output filenames.
                              E.g., ['Mimi.csv', 'Temitope_Joseph.csv', ...]
    """
    if not os.path.exists(input_filename):
        print(f"Error: Input file '{input_filename}' not found.")
        return

    try:
        df = pd.read_csv(input_filename)
        total_rows = len(df)
        print(f"Successfully loaded '{input_filename}' with {total_rows} rows.")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    num_parts = len(output_names)
    if num_parts != 10:
        print(f"Warning: Expected 10 output names, but received {num_parts}. Proceeding anyway.")

    # Calculate the number of rows for each part, rounding up for remainders
    rows_per_part = np.ceil(total_rows / num_parts).astype(int)

    # Initialize a list to keep track of generated files
    generated_files = []

    # Divide the DataFrame into parts and save them
    for i in range(num_parts):
        start_index = i * rows_per_part
        end_index = min((i + 1) * rows_per_part, total_rows)

        # Handle the case where there might not be enough rows for the last parts
        if start_index >= total_rows:
            print(f"No more rows to divide for part {i+1} ({output_names[i]}). Skipping.")
            continue

        part_df = df.iloc[start_index:end_index]
        output_filename = output_names[i]

        try:
            part_df.to_csv(output_filename, index=False)
            generated_files.append(output_filename)
            print(f"Generated '{output_filename}' with {len(part_df)} rows.")
        except Exception as e:
            print(f"Error saving '{output_filename}': {e}")

    print("\nCSV division complete!")
    print(f"The original file has been divided into {len(generated_files)} parts, and saved as: {', '.join(generated_files)}")
    print("Each part will contain an approximately equal number of rows. Any 'remainder' rows are distributed among the first few files.")

# --- Configuration ---
# IMPORTANT: Make sure this matches the actual filename of your uploaded CSV
input_csv_filename = 'Chat-Transcript_99d4c94e-bfbd-4c3e-8100-0b0d8f1f9b4e-1750806000000.csv'

# The names for your output files
output_csv_names = [
    'Mimi.csv',
    'Temitope_Joseph.csv',
    'Laycon.csv',
    'Ugochukwu.csv',
    'Abdushakur.csv',
    'Ayobami.csv',
    'Adoyi.csv',
    'Victoria.csv',
    'Maro.csv',
    'Obi.csv'
]

# Run the function
if __name__ == "__main__":
    divide_csv_file(input_csv_filename, output_csv_names)
