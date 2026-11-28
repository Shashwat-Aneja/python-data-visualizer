# Python Data Visualizer
A simple Python script that reads a CSV file and generates data visualizations such as bar charts and line graphs using `matplotlib`.

This project demonstrates data handling, Python scripting, visualization fundamentals, and automation.

---

## 📊 Features
- Reads CSV files
- Creates bar and line visualizations
- Optional: Auto-detect numeric columns
- Uses matplotlib
- Beginner-friendly & expandable

---

## 🚀 Usage

### 1. Clone Repo
```bash
git clone https://github.com/<your-username>/python-data-visualizer
cd python-data-visualizer
```

### 2. Install dependencies
```bash
pip install matplotlib pandas
```

### 3. Run script
```bash
python data_visualizer.py your_file.csv
```

---

## 📎 Example
Example CSV:
```
Name,Score
John,85
Alice,90
Bob,78
```

Output: A bar chart of scores.

---

## 📁 Project Structure
```
python-data-visualizer/
│
├── data_visualizer.py
└── README.md
```

---

## 🔧 Future Enhancements
- Support pie charts & histograms
- Export graphs as images
- Jupyter Notebook integration

---

Built by **Shashwat Aneja**

Plots are bounded to 1,000 evenly spaced observations by default, retaining both endpoints. Use `--max-points N` to control rendering cost; omitted points are not aggregated or interpolated.

`--x-column month --column sales` labels charts using another CSV column, preserving row order and alignment after missing numeric values are dropped.

When `--x-column` is given without `--column`, automatic metric selection excludes the X column. Numeric time/index columns therefore no longer get plotted against themselves.

Each PNG is rendered to a temporary file and atomically replaces its destination only after rendering succeeds. A failed render preserves that chart’s previous file; the two chart files are committed independently.

`--histogram` adds a distribution chart from all finite observations. Unlike the bar and line charts, histogram counts are not reduced by `--max-points`.

`--summary-output summary.json` atomically records input, usable, dropped and plotted row counts, plus full histogram coverage. The summary cannot alias the input CSV or chart outputs. This makes filtering and downsampling visible to batch users.

`--delimiter ";"`, `--delimiter tab` and `--delimiter "|"` support alternate input CSV separators, including quoted fields. Duplicate-header validation uses the selected separator. The default input and all CSV exports remain comma-separated.

`--x-column day --sort-x` stably orders X values before point sampling and plotting. Numeric values sort numerically and text labels lexically; the option does not infer or parse timestamps. Equal X values retain source order. Without the flag, source order is preserved.

Seekable caller-owned text and UTF-8 binary CSV streams now receive the same duplicate-header checks as file paths, before pandas can rename ambiguous columns. Validation restores the starting position and leaves caller streams open; nonseekable stream objects are rejected explicitly.

CSV paths ending in `.gz`, `.bz2`, or `.xz` are supported without unpacking a separate file. Header validation reads the same compression format as pandas and still rejects duplicate columns, including BOM-prefixed quoted headers and alternate delimiters. Archive containers such as ZIP/TAR are outside this feature.

`--log-y` renders bar and line Y axes logarithmically for strictly positive usable observations. Zero/negative values fail before chart output; they are not silently dropped to make the axis work. Histogram frequency axes remain linear.

`--chart-kind bar|line|both` selects the charts actually rendered, avoiding unnecessary rendering and file replacement. The default is both; `--histogram` is independent. Only requested chart destinations participate in collision checks.

Corrupt compressed bodies, invalid DEFLATE blocks and header-parser limit failures use the normal validation-error path rather than escaping as EOFError, zlib.error or csv.Error. Header inspection restores caller stream position/ownership on these failures. No invalid input is exported.

`--x-column date --parse-x-dates --sort-x` parses selected labels as timestamps normalized to UTC, then sorts chronologically with stable ties. Numeric epoch offsets and invalid labels are rejected explicitly. Without this option, X labels retain their original behavior.

`--summary-stats --summary-output summary.json` adds minimum, maximum, overflow-safe mean and median over every usable finite observation before plot-point sampling. Existing count-only summaries remain the default. Even medians and means remain finite for large representable values.

`--chart-kind histogram` renders only the full finite distribution, with no unnecessary bar/line rendering or point sampling. Its summary reports zero sampled plotted_rows and the full histogram_rows. X labels/sorting and logarithmic Y options are rejected as inapplicable in histogram-only mode.

### Optional raw CSV row budget

Use `--max-input-rows 100000` to reject an input file with more than that many data rows before modeling or export. The budget is per file, including comparison/training/scoring inputs, and applies before filtering or aggregation. The default remains unlimited. Values must be integers from 1 to 10,000,000. Only the budget plus one rows are loaded; oversized inputs fail rather than being silently truncated. This is a row limit, not a byte or field-size limit. Python callers can use `max_rows=`.

`--aggregate-x sum|mean` combines repeated explicit X labels before bar/line point sampling, keeping first-label order unless `--sort-x` is selected. Parsed date axes group equal UTC instants. Histogram and full-data statistics retain raw usable observations; summaries disclose aggregation and pre-sampling group count. Unrepresentable aggregate values fail before chart writes.
