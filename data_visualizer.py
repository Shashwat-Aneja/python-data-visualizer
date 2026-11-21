import csv
import argparse
import json
import re
import os
import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _reject_duplicate_headers(csv_file):
    """Do not let pandas silently rename ambiguous source CSV columns."""
    if isinstance(csv_file, (str, os.PathLike)) and Path(csv_file).is_file():
        with open(csv_file, encoding="utf-8-sig", newline="") as source:
            headers = next(csv.reader(source), [])
        if len(headers) != len(set(headers)):
            raise ValueError("CSV column names must be unique; duplicate headers are ambiguous.")


def select_numeric_series(data, column=None):
    """Choose a real-valued numeric column and return finite, non-missing observations."""
    if data.columns.duplicated().any():
        raise ValueError("Column names must be unique before selecting a numeric series.")
    if column is not None:
        if column not in data.columns:
            raise ValueError(f"Column {column!r} was not found in the CSV.")
        selected = data[column]
        if not pd.api.types.is_numeric_dtype(selected) or pd.api.types.is_complex_dtype(selected) or pd.api.types.is_bool_dtype(selected):
            raise ValueError(f"Column {column!r} is not numeric or contains unsupported complex values.")
        series = selected.dropna()
        series = series[np.isfinite(series.to_numpy(dtype=float))]
        if series.empty:
            raise ValueError(f"Numeric column {column!r} contains no usable values.")
        return column, series

    numeric_columns = [
        candidate
        for candidate in data.columns
        if pd.api.types.is_numeric_dtype(data[candidate])
        and not pd.api.types.is_complex_dtype(data[candidate])
        and not pd.api.types.is_bool_dtype(data[candidate])
    ]
    for candidate in numeric_columns:
        series = data[candidate].dropna()
        series = series[np.isfinite(series.to_numpy(dtype=float))]
        if not series.empty:
            return candidate, series
    if len(numeric_columns):
        raise ValueError("Real numeric columns contain no usable values.")
    raise ValueError("No supported real numeric columns found to visualize.")


def limit_plot_points(series, max_points):
    if not isinstance(max_points, int) or isinstance(max_points, bool) or max_points < 2:
        raise ValueError("max_points must be an integer of at least 2.")
    if len(series) <= max_points:
        return series
    return series.iloc[np.linspace(0, len(series) - 1, max_points, dtype=int)]


def save_chart_atomic(destination):
    """Preserve an existing PNG if rendering or filesystem replacement fails."""
    descriptor, temporary = tempfile.mkstemp(prefix=f".{destination.stem}.", suffix=".png", dir=destination.parent)
    os.close(descriptor)
    try:
        plt.savefig(temporary, dpi=150, bbox_inches="tight", format="png")
        os.replace(temporary, destination)
    finally:
        Path(temporary).unlink(missing_ok=True)


def visualize_data(csv_file, column=None, output_dir=None, max_points=1000, x_column=None, histogram=False, summary_output=None):
    owned_figures = []
    try:
        data = pd.read_csv(csv_file)
        _reject_duplicate_headers(csv_file)
        print(f"Loaded {csv_file} successfully!")
        print("Columns detected:", list(data.columns))

        selection_data = data
        if column is None and x_column is not None:
            if x_column not in data.columns:
                raise ValueError(f"X column {x_column!r} was not found.")
            selection_data = data.drop(columns=[x_column])
        selected_column, series = select_numeric_series(selection_data, column)
        if x_column is not None:
            if x_column not in data.columns:
                raise ValueError(f"X column {x_column!r} was not found.")
            labels = data.loc[series.index, x_column]
            if labels.isna().any():
                raise ValueError("X column contains missing labels for plotted rows.")
            series = series.copy()
            series.index = pd.Index(labels, name=x_column)
        usable_rows = len(series)
        distribution_values = series.to_numpy(dtype=float)
        series = limit_plot_points(series, max_points)
        print(f"📊 Visualizing column: {selected_column} ({len(series)} usable rows)")

        destination = None
        safe_name = None
        if output_dir is not None:
            destination = Path(output_dir).expanduser()
            destination.mkdir(parents=True, exist_ok=True)
            safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", selected_column).strip("_") or "metric"
            source = Path(csv_file).expanduser().resolve()
            kinds = ["bar", "line"] + (["histogram"] if histogram else [])
            for kind in kinds:
                output = destination / f"{safe_name}_{kind}.png"
                if output.resolve() == source or (output.exists() and output.samefile(source)):
                    raise ValueError("Chart outputs must not overwrite the source data file.")

        summary_path = Path(summary_output).expanduser().resolve() if summary_output is not None else None
        if summary_path is not None:
            protected = [Path(csv_file).expanduser().resolve()]
            if destination is not None:
                protected += [destination / f"{safe_name}_{kind}.png" for kind in (["bar", "line"] + (["histogram"] if histogram else []))]
            if any(summary_path == path.resolve() or (summary_path.exists() and path.exists() and summary_path.samefile(path)) for path in protected):
                raise ValueError("Summary output must differ from source data and chart outputs.")
        owned_figures.append(plt.figure())
        series.plot(kind="bar")
        plt.title(f"Bar Chart of {selected_column}")
        plt.xlabel(x_column or "Index")
        plt.ylabel(selected_column)
        plt.tight_layout()
        if destination is None:
            plt.show()
        else:
            save_chart_atomic(destination / f"{safe_name}_bar.png")
            plt.close()

        owned_figures.append(plt.figure())
        series.plot(kind="line")
        plt.title(f"Line Chart of {selected_column}")
        plt.xlabel(x_column or "Index")
        plt.ylabel(selected_column)
        plt.tight_layout()
        if destination is None:
            plt.show()
        else:
            save_chart_atomic(destination / f"{safe_name}_line.png")
            plt.close()
        if histogram:
            owned_figures.append(plt.figure())
            bin_count = min(100, max(1, int(np.ceil(np.sqrt(len(distribution_values))))))
            plt.hist(distribution_values, bins=bin_count)
            plt.title(f"Distribution of {selected_column}")
            plt.xlabel(selected_column)
            plt.ylabel("Frequency")
            plt.tight_layout()
            if destination is None:
                plt.show()
            else:
                save_chart_atomic(destination / f"{safe_name}_histogram.png")
                plt.close()
        if summary_path is not None:
            write_chart_summary({"column": selected_column, "input_rows": len(data), "usable_rows": usable_rows, "dropped_rows": len(data) - usable_rows, "plotted_rows": len(series), "histogram_rows": usable_rows if histogram else 0}, summary_path)
        return 0
    except (OSError, pd.errors.ParserError, ValueError) as exc:
        print(f"Error processing file: {exc}")
        return 1
    finally:
        for figure in owned_figures:
            plt.close(figure)


def write_chart_summary(payload, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=destination.parent, delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(payload, handle, allow_nan=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Create bar and line charts from a CSV file.")
    parser.add_argument("csv_file", help="Path to the input CSV file")
    parser.add_argument("--column", help="Name of the numeric column to visualize")
    parser.add_argument(
        "--output-dir",
        help="Save PNG charts to this directory instead of opening interactive windows",
    )
    parser.add_argument("--max-points", type=int, default=1000, help="Maximum points plotted, sampled evenly including both endpoints")
    parser.add_argument("--x-column", help="Column to use for row labels on the horizontal axis")
    parser.add_argument("--histogram", action="store_true", help="Also plot a distribution using every finite value, without point sampling")
    parser.add_argument("--summary-output", help="Atomically save numeric filtering and point-sampling counts as JSON")
    args = parser.parse_args(argv)
    options = {"histogram": True} if args.histogram else {}
    if args.summary_output:
        options["summary_output"] = args.summary_output
    return visualize_data(args.csv_file, column=args.column, output_dir=args.output_dir, max_points=args.max_points, x_column=args.x_column, **options)


if __name__ == "__main__":
    raise SystemExit(main())
