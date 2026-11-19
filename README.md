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
