import zlib
import gzip
import bz2
import lzma
import io
from numbers import Number
import csv
import argparse
import json
import math
from fractions import Fraction
import re
import os
import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _read_csv_input(csv_file, delimiter=",", max_rows=None, **options):
    if max_rows is not None and (isinstance(max_rows, bool) or not isinstance(max_rows, int) or not 1 <= max_rows <= 10_000_000):
        raise ValueError("max_rows must be an integer from 1 to 10000000.")
    if delimiter not in (",", ";", "\t", "|"):
        raise ValueError("Unsupported input delimiter.")
    if max_rows is not None:
        if "nrows" in options:
            raise ValueError("Do not combine nrows and max_rows.")
        options["nrows"] = max_rows + 1
    _reject_duplicate_headers(csv_file, delimiter)
    try:
        frame = pd.read_csv(csv_file, **options, **({"sep": delimiter} if delimiter != "," else {}))
    except (EOFError, lzma.LZMAError, zlib.error, csv.Error) as exc:
        raise ValueError("CSV input is corrupt or incomplete, or its header exceeds parser limits.") from exc
    if max_rows is not None and len(frame) > max_rows:
        raise ValueError("CSV input exceeds the configured row limit.")
    return frame


def _reject_duplicate_headers(csv_file, delimiter=","):
    """Inspect original UTF-8 CSV headers without taking ownership of streams."""
    def header_lines(source):
        # csv.reader needs physical lines even for StringIO objects whose default
        # iterator does not recognize CR-only records. Preserve quoted newlines.
        pending = ""
        first = True
        started = False
        while True:
            chars = []
            while True:
                char = pending or source.read(1)
                pending = ""
                if not char:
                    break
                if first:
                    first = False
                    if char == "\ufeff":
                        continue
                chars.append(char)
                if char == "\r":
                    following = source.read(1)
                    if following == "\n":
                        chars.append(following)
                    else:
                        pending = following
                    break
                if char == "\n":
                    break
            if not chars:
                return
            line = "".join(chars)
            if not started and not line.strip():
                continue
            started = True
            yield line

    if isinstance(csv_file, (str, os.PathLike)):
        if not Path(csv_file).is_file():
            return
        opener = {".gz": gzip.open, ".bz2": bz2.open, ".xz": lzma.open}.get(Path(csv_file).suffix, open)
        try:
            with opener(csv_file, mode="rt", encoding="utf-8-sig", newline="") as source:
                headers = next(csv.reader(header_lines(source), delimiter=delimiter), [])
        except (EOFError, lzma.LZMAError, zlib.error, csv.Error) as exc:
            raise ValueError("CSV input is corrupt or incomplete, or its header exceeds parser limits.") from exc
    else:
        if not all(hasattr(csv_file, name) for name in ("read", "seek", "tell")) or (hasattr(csv_file, "seekable") and not csv_file.seekable()):
            raise ValueError("CSV streams must be seekable for header validation.")
        position = csv_file.tell()
        binary = isinstance(csv_file.read(0), bytes)
        source = io.TextIOWrapper(csv_file, encoding="utf-8-sig", newline="") if binary else csv_file
        try:
            headers = next(csv.reader(header_lines(source), delimiter=delimiter), [])
        except (EOFError, lzma.LZMAError, zlib.error, csv.Error) as exc:
            raise ValueError("CSV input is corrupt or incomplete, or its header exceeds parser limits.") from exc
        finally:
            if binary:
                source.detach()
            csv_file.seek(position)
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


def _source_path(source):
    if isinstance(source, (str, os.PathLike)):
        return Path(source).expanduser().resolve()
    name = getattr(source, "name", None)
    return Path(name).expanduser().resolve() if isinstance(name, (str, os.PathLike)) else None


def _aliases_source(destination, source):
    path = _source_path(source)
    if path is not None and (destination.resolve() == path or (destination.exists() and path.exists() and destination.samefile(path))):
        return True
    if destination.exists() and hasattr(source, "fileno"):
        try:
            source_stat = os.fstat(source.fileno())
        except (OSError, ValueError):
            return False
        target_stat = destination.stat()
        return (source_stat.st_dev, source_stat.st_ino) == (target_stat.st_dev, target_stat.st_ino)
    return False


def visualize_data(csv_file, column=None, output_dir=None, max_points=1000, x_column=None, histogram=False, summary_output=None, delimiter=",", sort_x=False, log_y=False, chart_kind="both", parse_x_dates=False, summary_stats=False, max_rows=None, aggregate_x=None, data_output=None):
    owned_figures = []
    try:
        if aggregate_x is not None and (aggregate_x not in ("sum", "mean") or x_column is None or chart_kind == "histogram"):
            raise ValueError("aggregate_x requires an X column, a sum/mean policy and a bar or line chart.")
        if not isinstance(summary_stats, bool) or (summary_stats and summary_output is None):
            raise ValueError("summary_stats requires a summary_output destination and a boolean.")
        if not isinstance(parse_x_dates, bool) or (parse_x_dates and x_column is None):
            raise ValueError("parse_x_dates requires an explicit x_column and a boolean.")
        if not isinstance(chart_kind, str) or chart_kind not in {"bar", "line", "both", "histogram"}:
            raise ValueError("chart_kind must be bar, line, both, or histogram.")
        if chart_kind == "histogram":
            if x_column is not None or sort_x or log_y:
                raise ValueError("Histogram-only charts do not use X labels, X sorting, or logarithmic Y axes.")
            histogram = True
        kinds = ["histogram"] if chart_kind == "histogram" else (["bar", "line"] if chart_kind == "both" else [chart_kind]) + (["histogram"] if histogram else [])
        if not isinstance(log_y, bool):
            raise ValueError("log_y must be a boolean.")
        data = _read_csv_input(csv_file, delimiter, **({"max_rows": max_rows} if max_rows is not None else {}))
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
            if parse_x_dates:
                if labels.map(lambda value: isinstance(value, Number)).any():
                    raise ValueError("Date X labels must be calendar timestamps, not numeric epoch offsets.")
                labels = labels.map(lambda value: pd.to_datetime(value, errors="coerce", utc=True))
                if labels.isna().any():
                    raise ValueError("Date X labels must contain valid calendar timestamps.")
            series = series.copy()
            series.index = pd.Index(labels, name=x_column)
        if sort_x:
            if x_column is None:
                raise ValueError("Sorting X values requires an explicit x_column.")
            series = series.sort_index(kind="stable")
        if log_y and (series <= 0).any():
            raise ValueError("Logarithmic Y axes require strictly positive usable values.")
        usable_rows = len(series)
        distribution_values = series.to_numpy(dtype=float)
        aggregated_points = None
        if aggregate_x is not None:
            from fractions import Fraction
            def aggregate(values):
                numbers = [float(value) for value in values]
                try:
                    value = math.fsum(numbers)
                    if aggregate_x == "mean":
                        value /= len(numbers)
                except OverflowError:
                    exact = sum((Fraction.from_float(value) for value in numbers), Fraction())
                    value = float(exact / len(numbers) if aggregate_x == "mean" else exact)
                if not math.isfinite(value):
                    raise ValueError("Aggregated chart values exceed the supported numeric range.")
                return value
            series = series.groupby(level=0, sort=False).agg(aggregate)
            aggregated_points = len(series)
            if log_y and (series <= 0).any():
                raise ValueError("Logarithmic Y axes require positive aggregated values.")
        if chart_kind != "histogram":
            series = limit_plot_points(series, max_points)
        print(f"📊 Visualizing column: {selected_column} ({len(series)} usable rows)")

        destination = None
        safe_name = None
        if output_dir is not None:
            destination = Path(output_dir).expanduser()
            destination.mkdir(parents=True, exist_ok=True)
            safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", selected_column).strip("_") or "metric"
            for kind in kinds:
                output = destination / f"{safe_name}_{kind}.png"
                if _aliases_source(output, csv_file):
                    raise ValueError("Chart outputs must not overwrite the source data file.")

        summary_path = Path(summary_output).expanduser().resolve() if summary_output is not None else None
        if summary_path is not None:
            protected = []
            if destination is not None:
                protected += [destination / f"{safe_name}_{kind}.png" for kind in kinds]
            if _aliases_source(summary_path, csv_file) or any(summary_path == path.resolve() or (summary_path.exists() and path.exists() and summary_path.samefile(path)) for path in protected):
                raise ValueError("Summary output must differ from source data and chart outputs.")
        data_path = Path(data_output).expanduser().resolve() if data_output is not None else None
        if data_path is not None:
            protected = []
            if summary_path is not None:
                protected.append(summary_path)
            if destination is not None:
                protected += [destination / f"{safe_name}_{kind}.png" for kind in kinds]
            if _aliases_source(data_path, csv_file) or any(data_path == path.resolve() or (data_path.exists() and path.exists() and data_path.samefile(path)) for path in protected):
                raise ValueError("Data output must differ from the source, summary and chart outputs.")
            data_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", dir=data_path.parent, delete=False) as handle:
                    temporary = Path(handle.name)
                    pd.DataFrame({"x": series.index, "value": series.to_numpy()}).to_csv(handle, index=False)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, data_path)
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
        if chart_kind in {"bar", "both"}:
            owned_figures.append(plt.figure())
            series.plot(kind="bar", **({"logy": True} if log_y else {}))
            plt.title(f"Bar Chart of {selected_column}")
            plt.xlabel(x_column or "Index")
            plt.ylabel(selected_column)
            plt.tight_layout()
            if destination is None:
                plt.show()
            else:
                save_chart_atomic(destination / f"{safe_name}_bar.png")
                plt.close()

        if chart_kind in {"line", "both"}:
            owned_figures.append(plt.figure())
            series.plot(kind="line", **({"logy": True} if log_y else {}))
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
            payload = {"column": selected_column, "input_rows": len(data), "usable_rows": usable_rows, "dropped_rows": len(data) - usable_rows, "plotted_rows": 0 if chart_kind == "histogram" else len(series), "histogram_rows": usable_rows if histogram else 0}
            if aggregate_x is not None:
                payload.update(aggregation=aggregate_x, aggregated_points=aggregated_points)
            if summary_stats:
                payload["statistics"] = numeric_statistics(distribution_values)
            write_chart_summary(payload, summary_path)
        return 0
    except (OSError, pd.errors.ParserError, ValueError, OverflowError) as exc:
        print(f"Error processing file: {exc}")
        return 1
    finally:
        for figure in owned_figures:
            plt.close(figure)


def numeric_statistics(values):
    values = np.asarray(values, dtype=float)
    if not values.size or not np.isfinite(values).all():
        raise ValueError("Statistics require non-empty finite observations.")
    def mean(numbers):
        try:
            return math.fsum(float(value) for value in numbers) / len(numbers)
        except OverflowError:
            # Preserve cancellation and tiny residuals before rounding the mean.
            total = sum((Fraction.from_float(float(value)) for value in numbers), Fraction())
            return float(total / len(numbers))
    ordered = np.sort(values)
    middle = len(ordered) // 2
    median = float(ordered[middle]) if len(ordered) % 2 else mean(ordered[middle - 1:middle + 1])
    return {"minimum": float(ordered[0]), "maximum": float(ordered[-1]), "mean": mean(values), "median": median}


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
    parser.add_argument("--delimiter", choices=(",", ";", "tab", "|"), default=",", help="Input CSV delimiter; exports remain comma-separated")
    parser.add_argument("--sort-x", action="store_true", help="Stably sort explicit X values before sampling and plotting")
    parser.add_argument("--log-y", action="store_true", help="Use logarithmic Y axes for positive bar/line values; histogram counts stay linear")
    parser.add_argument("--chart-kind", choices=("bar", "line", "both", "histogram"), default="both", help="Render only the needed chart types (histogram remains independently opt-in)")
    parser.add_argument("--parse-x-dates", action="store_true", help="Parse explicit X labels as UTC timestamps before optional chronological sorting")
    parser.add_argument("--summary-stats", action="store_true", help="Include full finite-data extrema, mean and median in --summary-output")
    parser.add_argument("--max-input-rows", type=int, help="Reject CSV files exceeding this raw row budget (1..10000000)")
    parser.add_argument("--aggregate-x", choices=("sum", "mean"), help="Aggregate repeated X labels before point sampling")
    parser.add_argument("--data-output", help="Atomically export the actual chart series as x,value CSV")
    args = parser.parse_args(argv)
    if args.max_input_rows is not None and not 1 <= args.max_input_rows <= 10_000_000:
        parser.error("--max-input-rows must be from 1 to 10000000")
    delimiter = "\t" if args.delimiter == "tab" else args.delimiter
    options = {"histogram": True} if args.histogram else {}
    if args.summary_stats:
        options["summary_stats"] = True
    if args.parse_x_dates:
        options["parse_x_dates"] = True
    if args.chart_kind != "both":
        options["chart_kind"] = args.chart_kind
    if args.log_y:
        options["log_y"] = True
    if args.sort_x:
        options["sort_x"] = True
    if args.data_output is not None:
        options["data_output"] = args.data_output
    if args.aggregate_x is not None:
        options["aggregate_x"] = args.aggregate_x
    if args.max_input_rows is not None:
        options["max_rows"] = args.max_input_rows
    if delimiter != ",":
        options["delimiter"] = delimiter
    if args.summary_output:
        options["summary_output"] = args.summary_output
    return visualize_data(args.csv_file, column=args.column, output_dir=args.output_dir, max_points=args.max_points, x_column=args.x_column, **options)


if __name__ == "__main__":
    raise SystemExit(main())
