# BCG Screenshot Processor

Automated tool for processing security event reports, extracting screenshots from videos, and generating Excel reports.

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Prepare data**:
   - Place files in the `data/` directory
   - Required files:
     - `EventsReportFrom_YYYY-MM-DD_*.csv` (events list)
     - `Event_Report_SERVER_from_*_to_*.zip` (video archives)

3. **Run**:
   ```bash
   python main.py
   ```

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
- ✅ **Coverage Analysis**: Checks if ZIP files cover all events
- ✅ **Gap Detection**: Identifies missing time periods
- ✅ **Multi-Server Support**: Processes multiple servers automatically
- ✅ **Excel Generation**: Creates reports with clickable screenshot links
- ✅ **Automatic Cleanup**: Removes temporary files
- ✅ **Extensible Design**: Easy to add new features or modify existing ones

## Example Data Structure

```
data/
├── EventsReportFrom 2025-06-11 00_00_00 To 2025-06-11 23_59_00.csv
├── Event_Report_server_from_2025-06-11-00-00-00_to_2025-06-11-18-43-59.zip
└── Event_Report_server_from_2025-06-11-18-44-00_to_2025-06-11-23-59-59.zip
```

### Sample CSV Content:
```csv
Name;Description;Date/Time;End Date/Time;True Event
server14-4;STOP;2025-06-11 18:47:52;2025-06-11 18:49:54;UNMARKED_EVT
server16-4;QUEUE;2025-06-11 18:45:51;2025-06-11 18:48:11;UNMARKED_EVT
```

## Output Structure

```
2025-06-11_2025-06-11/
└── server/
    ├── screenshots/
    │   ├── server14-4_STOP_2025-06-11-18-47-52.png
    │   └── server16-4_QUEUE_2025-06-11-18-45-51.png
    ├── video/
    │   ├── server14-4_STOP_2025-06-11-18-47-52.mkv
    │   └── server16-4_QUEUE_2025-06-11-18-45-51.mkv
    ├── eventReports/
    │   ├── server14-4_STOP_2025-06-11-18-47-52_eventSnapshot.jpg
    │   └── server16-4_QUEUE_2025-06-11-18-45-51_eventSnapshot.jpg
    └── server_events_report.xlsx
```

## Configuration

Default settings can be modified in `config.py`:
- Screenshot timestamp: 13 seconds
- Supported video formats: `.mkv`
- CSV separators: `;` and `,` (auto-detected)
- DateTime parsing formats

## Development

The modular structure makes it easy to:
- Add new video formats in `video_processing.py`
- Modify report formats in `excel_report.py`
- Enhance coverage analysis in `coverage_analyzer.py`
- Add new file operations in `file_utils.py`

Each module has a single responsibility and clear interfaces, making the codebase maintainable and extensible.