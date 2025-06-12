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
   python process_events.py
   ```

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
    ├── media/
    │   ├── screenshots/
    │   │   ├── server14-4_STOP_2025-06-11-18-47-52.png
    │   │   └── server16-4_QUEUE_2025-06-11-18-45-51.png
    │   └── video/
    │       ├── server14-4_STOP_2025-06-11-18-47-52.mkv
    │       └── server16-4_QUEUE_2025-06-11-18-45-51.mkv
    └── server_events_report.xlsx
```

## Features

- ✅ **Coverage Analysis**: Checks if ZIP files cover all events
- ✅ **Gap Detection**: Identifies missing time periods
- ✅ **Multi-Server Support**: Processes multiple servers automatically
- ✅ **Excel Generation**: Creates reports with clickable screenshot links
- ✅ **Automatic Cleanup**: Removes temporary files

## Configuration

- Screenshot timestamp: Default 13 seconds (configurable in `MultiServerEventProcessor(screenshot_timestamp=13)`)
- Supported video formats: `.mkv`
- CSV separators: `;` and `,` (auto-detected)