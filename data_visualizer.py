import argparse
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def select_numeric_series(data, column=None):
    """Choose a numeric column and return finite, non-missing observations."""
    if column is not None:
        if column not in data.columns:
            raise ValueError(f"Column {column!r} was not found in the CSV.")
        if not pd.api.types.is_numeric_dtype(data[column]):
            raise ValueError(f"Column {column!r} is not numeric.")
        series = data[column].dropna()
        series = series[np.isfinite(series.to_numpy(dtype=float))]
        if series.empty:
            raise ValueError(f"Numeric column {column!r} contains no usable values.")
        return column, series

    numeric_columns = data.select_dtypes(include=["number"]).columns
    for candidate in numeric_columns:
        series = data[candidate].dropna()
        series = series[np.isfinite(series.to_numpy(dtype=float))]
        if not series.empty:
            return candidate, series
    if len(numeric_columns):
        raise ValueError("Numeric columns contain no usable values.")
    raise ValueError("No numeric columns found to visualize.")


def visualize_data(csv_file, column=None, output_dir=None):
    try:
        data = pd.read_csv(csv_file)
        print(f"Loaded {csv_file} successfully!")
        print("Columns detected:", list(data.columns))

        selected_column, series = select_numeric_series(data, column)
        print(f"📊 Visualizing column: {selected_column} ({len(series)} usable rows)")

        destination = None
        safe_name = None
        if output_dir is not None:
            destination = Path(output_dir).expanduser()
            destination.mkdir(parents=True, exist_ok=True)
            safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", selected_column).strip("_") or "metric"

        plt.figure()
        series.plot(kind="bar")
        plt.title(f"Bar Chart of {selected_column}")
        plt.xlabel("Index")
        plt.ylabel(selected_column)
        plt.tight_layout()
        if destination is None:
            plt.show()
        else:
            plt.savefig(destination / f"{safe_name}_bar.png", dpi=150, bbox_inches="tight")
            plt.close()

        plt.figure()
        series.plot(kind="line")
        plt.title(f"Line Chart of {selected_column}")
        plt.xlabel("Index")
        plt.ylabel(selected_column)
        plt.tight_layout()
        if destination is None:
            plt.show()
        else:
            plt.savefig(destination / f"{safe_name}_line.png", dpi=150, bbox_inches="tight")
            plt.close()
    except (OSError, pd.errors.ParserError, ValueError) as exc:
        print(f"Error processing file: {exc}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Create bar and line charts from a CSV file.")
    parser.add_argument("csv_file", help="Path to the input CSV file")
    parser.add_argument("--column", help="Name of the numeric column to visualize")
    parser.add_argument(
        "--output-dir",
        help="Save PNG charts to this directory instead of opening interactive windows",
    )
    args = parser.parse_args(argv)
    visualize_data(args.csv_file, column=args.column, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
