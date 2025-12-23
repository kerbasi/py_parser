# Log Metrics Parser

This tool automatically parses log files from a specified directory, extracts key metrics using regular expressions, and aggregates the results into a CSV report.

## Features

- **Recursive Scanning**: Traverses through all subdirectories of the designated log folder.
- **Smart Filtering**:
  - Processes `.log`, `.txt`, and `.gz` files.
  - Skips "SUMMARY" and "led" files.
  - Filters files by modification date (default: from 2025-01-01).
- **Metric Extraction**:
  - Supports extraction by numeric ID (e.g., `49.2.2`).
  - Supports extraction by textual name (e.g., `asic1_asic_total_power`).
  - Handles various log formats with different separators.
- **Output**: Generates a clean `ft_metrics_final.csv` file with aligned columns.

## Requirements

- Python 3.x
- pandas

Install dependencies:
```bash
pip install pandas
```

## Configuration

Open `main.py` and adjust the configuration section at the top of the file:

```python
# 1. Path to logs folder
ROOT_LOG_DIR = r'C:\logs' 

# 2. Start Date (ignore older files)
START_DATE_STR = '2025-01-01'

# 3. Metrics to extract
METRICS_LIST = [
    ('49.2.2', 'VDD_ASIC1_VOUT_Voltage'), 
    # ... add more metrics here
]
```

## Usage

Run the script from the terminal:

```bash
python main.py
```

The script will:
1. Scan the directories.
2. Print progress every 50 files.
3. Show a preview of the results.
4. Save the full report to `ft_metrics_final.csv`.
