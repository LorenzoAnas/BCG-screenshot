# BCG Screenshot Processor

Automated tool for processing security event reports, extracting screenshots from videos, and generating Excel reports. **Now supports CSV-only processing** when video archives are not available.

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Prepare data**:
   - Place files in the `data/` directory
   - Required files:
     - `EventsReportFrom_YYYY-MM-DD_*.csv` (events list) - **Required**
     - `Event_Report_SERVER_from_*_to_*.zip` (video archives) - *Optional*

3. **Run**:
   ```bash
   python main.py
   ```

## Processing Modes

### Full Processing (CSV + ZIP files)
When both CSV files and ZIP archives are present:
- ✅ Extracts screenshots from videos at 13-second mark
- ✅ Copies video files with organized naming
- ✅ Copies event snapshots
- ✅ Creates Excel reports with clickable screenshot links
- ✅ Performs coverage analysis to detect gaps

### CSV-Only Processing
When only CSV files are present (no ZIP archives):
- ✅ Processes all event data from CSV files
- ✅ Creates Excel reports with event details and timestamps
- ✅ Groups events by server automatically
- ✅ Generates merged reports across all servers
- ✅ Provides complete event categorization summary
- ⚠️ No screenshots, videos, or event snapshots

## Project Structure

```
bcg-screenshot-processor/
├── main.py                # Entry point
├── config.py              # Configuration settings
├── requirements.txt       # Dependencies
├── data/                  # Input files directory
└── src/                   # Source code modules
    ├── __init__.py        # Package initialization
    ├── file_utils.py      # File operations and ZIP handling
    ├── video_processing.py# Video screenshot extraction
    ├── event_processor.py # Main processing logic
    ├── coverage_analyzer.py # Coverage analysis
    ├── excel_report.py    # Excel report generation
    └── summary_generator.py # Summary reports
```

## Module Overview

### Core Modules

- **`main.py`** - Application entry point with user interface
- **`config.py`** - Centralized configuration constants
- **`src/event_processor.py`** - Main orchestration logic for processing events
- **`src/file_utils.py`** - File system operations, ZIP extraction, directory scanning
- **`src/video_processing.py`** - Video processing and screenshot extraction
- **`src/coverage_analyzer.py`** - Analysis of event coverage by ZIP files
- **`src/excel_report.py`** - Excel report generation with hyperlinks
- **`src/summary_generator.py`** - Final summary and statistics display

### Key Features

- ✅ **Modular Architecture**: Clean separation of concerns across modules
- ✅ **Flexible Processing**: Works with or without video archives
- ✅ **Coverage Analysis**: Checks if ZIP files cover all events (when available)
- ✅ **Gap Detection**: Identifies missing time periods in video coverage
- ✅ **Multi-Server Support**: Processes multiple servers automatically
- ✅ **Excel Generation**: Creates reports with clickable screenshot links
- ✅ **Precise Timestamps**: Full datetime precision including seconds
- ✅ **Automatic Cleanup**: Removes temporary files
- ✅ **Extensible Design**: Easy to add new features or modify existing ones

## Example Data Structure

```
data/
├── EventsReportFrom 2025-07-16 00_00_00 To 2025-07-22 23_59_00 (1).csv
├── EventsReportFrom 2025-07-16 00_00_00 To 2025-07-22 23_59_00 (2).csv
├── Event_Report_server_from_2025-07-16-00-00-00_to_2025-07-22-23-59-59.zip (optional)
└── Event_Report_server_from_2025-07-16-00-00-00_to_2025-07-22-23-59-59.zip (optional)
```

### Sample CSV Content:
```csv
Name;Description;Date/Time;End Date/Time;True Event
server5-2;WRONGWAY;2025-07-22 16:49:55;2025-07-22 16:55:04;UNMARKED_EVT
server7-2;CONGESTED;2025-07-22 14:56:13;2025-07-22 14:59:11;UNMARKED_EVT
```

## Output Structure

### With ZIP Files (Full Processing)
```
2025-07-16_2025-07-22_data/
└── server/
    ├── screenshots/
    │   ├── server5-2_WRONGWAY_2025-07-22-16-49-55.png
    │   └── server7-2_CONGESTED_2025-07-22-14-56-13.png
    ├── video/
    │   ├── server5-2_WRONGWAY_2025-07-22-16-49-55.mkv
    │   └── server7-2_CONGESTED_2025-07-22-14-56-13.mkv
    ├── eventReports/
    │   ├── server5-2_WRONGWAY_2025-07-22-16-49-55_eventSnapshot.jpg
    │   └── server7-2_CONGESTED_2025-07-22-14-56-13_eventSnapshot.jpg
    ├── server_events_report.xlsx
    └── complete_events_report.xlsx (merged)
```

### CSV-Only Processing
```
├── merged_events_report_csv_only_data.xlsx (all events from all servers)
```

Note: Output folder names now include the input directory name (e.g., "_data" when using the default "data" input folder, or "_custom_folder" when using a custom input directory named "custom_folder").

## Excel Report Format

All Excel reports include precise timestamps with seconds:

| Server | Name | Description | Date/Time | End Date/Time | True Event | Screenshot |
|--------|------|-------------|-----------|---------------|------------|------------|
| server | server5-2 | WRONGWAY | 22/07/2025 16:49:55 | 22/07/2025 16:55:04 | UNMARKED_EVT | [Link] |
| server | server7-2 | CONGESTED | 22/07/2025 14:56:13 | 22/07/2025 14:59:11 | UNMARKED_EVT | [Link] |

## Configuration

Default settings can be modified in `config.py`:
- Screenshot timestamp: 13 seconds
- Supported video formats: `.mkv`
- CSV separators: `;` and `,` (auto-detected)
- DateTime parsing formats (supports multiple formats including seconds)

## Usage Scenarios

### 1. Full Analysis (Recommended)
Place both CSV and ZIP files in `data/` directory for complete processing with screenshots and videos. Output will be in folders named like `2025-07-16_2025-07-22_data/`.

### 2. Quick Event Analysis
Place only CSV files in `data/` directory when you need:
- Event categorization and counting
- Timeline analysis
- Multi-server event correlation
- Excel reports for further analysis
Output file will be named like `merged_events_report_csv_only_data.xlsx`.

### 3. Partial Coverage
Mix of CSV files and some ZIP files - the tool will process what's available and clearly indicate coverage gaps. Output folders will be named with the input directory suffix.

## Development

The modular structure makes it easy to:
- Add new video formats in `video_processing.py`
- Modify report formats in `excel_report.py`
- Enhance coverage analysis in `coverage_analyzer.py`
- Add new file operations in `file_utils.py`
- Extend CSV parsing for new datetime formats in `event_processor.py`

Each module has a single responsibility and clear interfaces, making the codebase maintainable and extensible.