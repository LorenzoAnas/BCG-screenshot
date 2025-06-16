import os
import re
import zipfile
from datetime import datetime

def extract_server_from_sensor_name(sensor_name):
    """Extract server ID from sensor name (first 8 characters)."""
    if len(sensor_name) >= 8:
        return sensor_name[:8]
    return None

def parse_zip_info(zip_filename):
    """Extract server ID and time range from ZIP filename."""
    # Pattern: Event_Report_server_from_date-time_to_date-time.zip
    pattern = r'Event_Report_([^_]+)_from_(\d{4}-\d{2}-\d{2})-(\d{2})-(\d{2})-(\d{2})_to_(\d{4}-\d{2}-\d{2})-(\d{2})-(\d{2})-(\d{2})'
    match = re.search(pattern, zip_filename)
    
    if match:
        server_id = match.group(1)
        start_date = match.group(2)
        start_time = f"{match.group(3)}:{match.group(4)}:{match.group(5)}"
        end_date = match.group(6)
        end_time = f"{match.group(7)}:{match.group(8)}:{match.group(9)}"
        
        start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M:%S")
        end_datetime = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M:%S")
        
        return {
            'server_id': server_id,
            'start_datetime': start_datetime,
            'end_datetime': end_datetime,
            'start_date': start_date,
            'end_date': end_date
        }
    return None

def scan_directory(directory):
    """Scan directory for ZIP files and CSV files."""
    zip_files = []
    csv_files = []
    
    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        
        if file.endswith('.zip') and 'Event_Report' in file:
            zip_info = parse_zip_info(file)
            if zip_info:
                zip_info['filename'] = file
                zip_info['filepath'] = file_path
                zip_files.append(zip_info)
                print(f"Found ZIP: {file} - Server: {zip_info['server_id']}")
        
        elif file.startswith("EventsReportFrom") and file.endswith(".csv"):
            csv_files.append(file_path)
            print(f"Found CSV: {file}")
    
    # Group ZIP files by server
    zip_files_by_server = {}
    for zip_info in zip_files:
        server_id = zip_info['server_id']
        if server_id not in zip_files_by_server:
            zip_files_by_server[server_id] = []
        zip_files_by_server[server_id].append(zip_info)
    
    # Sort ZIP files by start time for each server
    for server_id in zip_files_by_server:
        zip_files_by_server[server_id].sort(key=lambda x: x['start_datetime'])
    
    return zip_files_by_server, csv_files

def extract_and_process_zip(zip_info, temp_base_dir):
    """Extract ZIP file and return the media directory path."""
    zip_path = zip_info['filepath']
    
    # Create unique temporary directory
    temp_dir = os.path.join(temp_base_dir, f"temp_{zip_info['server_id']}_{zip_info['start_datetime'].strftime('%Y%m%d_%H%M%S')}")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
    except zipfile.BadZipFile as e:
        print(f"❌ Corrupted ZIP file: {zip_info['filename']}")
        print(f"   Error: {e}")
        print(f"   Please re-upload/re-download this ZIP file")
        return None, temp_dir
    except Exception as e:
        print(f"❌ Error extracting ZIP file: {zip_info['filename']}")
        print(f"   Error: {e}")
        return None, temp_dir
    
    # Find the Event_Report directory
    event_report_dir = None
    for item in os.listdir(temp_dir):
        item_path = os.path.join(temp_dir, item)
        if os.path.isdir(item_path) and item.startswith("Event_Report_"):
            event_report_dir = item_path
            break
    
    if event_report_dir:
        media_dir = os.path.join(event_report_dir, "media")
        return media_dir, temp_dir
    
    return None, temp_dir
