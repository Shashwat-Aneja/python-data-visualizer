import pandas as pd
import matplotlib.pyplot as plt
import sys

def visualize_data(csv_file):
    try:
        data = pd.read_csv(csv_file)
        print(f"Loaded {csv_file} successfully!")
        print("Columns detected:", list(data.columns))

        numeric_cols = data.select_dtypes(include=['number']).columns
        if len(numeric_cols) == 0:
            print("❌ No numeric columns found to visualize.")
            return
        
        # Plot the first numeric column
        column = numeric_cols[0]
        series = data[column].dropna()
        if series.empty:
            print(f"❌ Numeric column {column!r} contains no usable values.")
            return
        print(f"📊 Visualizing column: {column} ({len(series)} usable rows)")

        plt.figure()
        series.plot(kind="bar")
        plt.title(f"Bar Chart of {column}")
        plt.xlabel("Index")
        plt.ylabel(column)
        plt.show()

        plt.figure()
        series.plot(kind="line")
        plt.title(f"Line Chart of {column}")
        plt.xlabel("Index")
        plt.ylabel(column)
        plt.show()

    except Exception as e:
        print(f"Error processing file: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python data_visualizer.py <csv_file>")
    else:
        visualize_data(sys.argv[1])
