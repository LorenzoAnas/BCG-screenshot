import os
import re
import csv
import zipfile
import shutil
from datetime import datetime, timedelta
import pandas as pd
from extract_screenshot import extract_screenshot

class MultiServerEventProcessor:
    def __init__(self, screenshot_timestamp=13):
        self.screenshot_timestamp = screenshot_timestamp
    
    def extract_server_from_sensor_name(self, sensor_name):
        """Extract server ID from sensor name (first 8 characters)."""
        if len(sensor_name) >= 8:
            return sensor_name[:8]
        return None
    
    def parse_zip_info(self, zip_filename):
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
    
    def read_and_group_events_by_server(self, csv_path):
        """Read events from CSV and group them by server."""
        if not os.path.exists(csv_path):
            print(f"CSV file not found: {csv_path}")
            return {}
        
        # Detect separator
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            first_line = f.readline()
            separator = ';' if ';' in first_line else ','
            print(f"DEBUG: Detected separator: '{separator}'")
        
        # Read all events and group by server
        events_by_server = {}
        
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=separator)
            print(f"DEBUG: CSV headers: {reader.fieldnames}")
            
            for i, row in enumerate(reader):
                # Get sensor name - handle both 'Name' and potential BOM issues
                sensor_name = ''
                for key in row.keys():
                    if 'Name' in key:  # This will match both 'Name' and '\ufeffName'
                        sensor_name = row[key].strip()
                        break
                
                if not sensor_name:
                    print(f"Warning: Empty sensor name in row {i}")
                    continue
                
                # Extract server ID
                server_id = self.extract_server_from_sensor_name(sensor_name)
                
                if not server_id:
                    print(f"Warning: Could not extract server ID from sensor name: '{sensor_name}'")
                    continue
                
                # Debug first few rows
                if i < 3:
                    print(f"DEBUG: Row {i}: Sensor='{sensor_name}', Server='{server_id}'")
                
                # Parse datetime
                try:
                    event_datetime = datetime.strptime(row['Date/Time'], "%Y-%m-%d %H:%M:%S")
                    row['datetime_obj'] = event_datetime
                except Exception as e:
                    print(f"Warning: Could not parse datetime for row {i}: {row.get('Date/Time', '')} - {e}")
                    continue
                
                # Initialize server group if not exists
                if server_id not in events_by_server:
                    events_by_server[server_id] = []
                
                # Store the clean sensor name and global index
                row['Name'] = sensor_name
                row['global_index'] = len(events_by_server[server_id])  # Global index for this server
                
                # Add to server group
                events_by_server[server_id].append(row)
        
        # Print summary
        for server_id, events in events_by_server.items():
            print(f"DEBUG: Server {server_id}: {len(events)} events")
        
        return events_by_server
    
    def scan_directory(self, directory):
        """Scan directory for ZIP files and CSV files."""
        zip_files = []
        csv_files = []
        
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            
            if file.endswith('.zip') and 'Event_Report' in file:
                zip_info = self.parse_zip_info(file)
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
    
    def check_coverage_for_server(self, server_id, events, zip_files):
        """Check if ZIP files cover all events for a specific server."""
        print(f"\n=== Coverage Analysis for Server: {server_id} ===")
        print(f"Found {len(events)} events for server {server_id}")
        print(f"Found {len(zip_files)} ZIP files for server {server_id}")
        
        if not zip_files:
            print(f"❌ No ZIP files found for server {server_id}")
            return {
                'total_events': len(events),
                'covered_events': [],
                'uncovered_events': events,
                'gaps': [],
                'zip_files': []
            }
        
        # Check coverage and assign ZIP-specific media indices
        covered_events = []
        uncovered_events = []
        gaps = []
        
        # Group events by ZIP file first to assign correct media indices
        events_by_zip = {}
        
        for event in events:
            event_time = event['datetime_obj']
            covered = False
            
            for zip_info in zip_files:
                if zip_info['start_datetime'] <= event_time <= zip_info['end_datetime']:
                    zip_filename = zip_info['filename']
                    if zip_filename not in events_by_zip:
                        events_by_zip[zip_filename] = []
                    
                    # Assign media index relative to this specific ZIP file
                    zip_media_index = len(events_by_zip[zip_filename])
                    event['zip_media_index'] = zip_media_index
                    
                    events_by_zip[zip_filename].append(event)
                    covered_events.append({
                        'event': event,
                        'zip_file': zip_filename
                    })
                    covered = True
                    break
            
            if not covered:
                uncovered_events.append(event)
        
        # Find gaps between ZIP files
        if len(zip_files) > 1:
            for i in range(len(zip_files) - 1):
                current_end = zip_files[i]['end_datetime']
                next_start = zip_files[i + 1]['start_datetime']
                
                if current_end < next_start:
                    gap_duration = next_start - current_end
                    if gap_duration > timedelta(minutes=1):  # Ignore small gaps
                        gaps.append({
                            'start': current_end,
                            'end': next_start,
                            'duration': gap_duration
                        })
        
        # Print summary
        print(f"Covered events: {len(covered_events)}/{len(events)}")
        print(f"Uncovered events: {len(uncovered_events)}")
        print(f"Time gaps: {len(gaps)}")
        
        # Debug: Show events per ZIP
        for zip_filename, zip_events in events_by_zip.items():
            print(f"DEBUG: {zip_filename}: {len(zip_events)} events (media indices 0-{len(zip_events)-1})")
        
        if uncovered_events:
            print("⚠️  UNCOVERED EVENTS:")
            for event in uncovered_events:
                print(f"  - {event['Name']} at {event['Date/Time']}")
        
        if gaps:
            print("⚠️  TIME GAPS:")
            for gap in gaps:
                print(f"  - {gap['start']} to {gap['end']} (Duration: {gap['duration']})")
        
        if len(covered_events) == len(events) and not gaps:
            print("✅ Complete coverage!")
        
        return {
            'total_events': len(events),
            'covered_events': covered_events,
            'uncovered_events': uncovered_events,
            'gaps': gaps,
            'zip_files': zip_files,
            'events_by_zip': events_by_zip
        }
    
    def extract_and_process_zip(self, zip_info, temp_base_dir):
        """Extract ZIP file and return the media directory path."""
        zip_path = zip_info['filepath']
        
        # Create unique temporary directory
        temp_dir = os.path.join(temp_base_dir, f"temp_{zip_info['server_id']}_{zip_info['start_datetime'].strftime('%Y%m%d_%H%M%S')}")
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
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
    
    def create_excel_with_links(self, data, output_path):
        """Create Excel file with clickable links to screenshots."""
        df = pd.DataFrame(data)
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Events', index=False)
            
            workbook = writer.book
            worksheet = writer.sheets['Events']
            
            # Make screenshot column clickable with relative paths
            if 'Screenshot' in df.columns:
                screenshot_col = df.columns.get_loc('Screenshot') + 1
                
                for row_idx, screenshot_path in enumerate(df['Screenshot'], start=2):
                    if screenshot_path:  # Check if path exists
                        cell = worksheet.cell(row=row_idx, column=screenshot_col)
                        # Create proper relative path for Excel
                        # Excel expects forward slashes and relative paths without leading ./
                        relative_path = screenshot_path.replace('\\', '/')
                        cell.hyperlink = relative_path
                        cell.style = "Hyperlink"
                        # Set the displayed text to just the filename
                        cell.value = os.path.basename(screenshot_path)
    
    def process_multiple_servers(self, directory):
        """Main processing function for multiple servers and ZIP files."""
        print("🔍 Scanning directory...")
        
        # Scan directory
        zip_files_by_server, csv_files = self.scan_directory(directory)
        
        if not csv_files:
            print("❌ No CSV files found!")
            return False
        
        if not zip_files_by_server:
            print("❌ No ZIP files found!")
            return False
        
        # Process each CSV file
        for csv_file in csv_files:
            print(f"\n📊 Processing CSV: {os.path.basename(csv_file)}")
            
            # Read and group events by server
            events_by_server = self.read_and_group_events_by_server(csv_file)
            
            if not events_by_server:
                print("❌ No events found in CSV!")
                continue
            
            print(f"Found events for servers: {list(events_by_server.keys())}")
            
            # Check coverage for each server
            coverage_reports = {}
            for server_id, events in events_by_server.items():
                zip_files = zip_files_by_server.get(server_id, [])
                coverage_reports[server_id] = self.check_coverage_for_server(server_id, events, zip_files)
            
            # Ask user to continue if there are issues
            has_issues = any(
                len(report['uncovered_events']) > 0 or len(report['gaps']) > 0
                for report in coverage_reports.values()
            )
            
            if has_issues:
                response = input("\n⚠️  Coverage issues detected. Continue processing? (y/n): ")
                if response.lower() != 'y':
                    continue
            
            # Process each server
            temp_base_dir = os.path.join(directory, "temp_processing")
            os.makedirs(temp_base_dir, exist_ok=True)
            
            try:
                for server_id, report in coverage_reports.items():
                    if not report['covered_events']:
                        print(f"⚠️  No covered events for server {server_id}, skipping...")
                        continue
                    
                    print(f"\n🔄 Processing server: {server_id}")
                    
                    # Determine date range from ZIP files
                    zip_files = report['zip_files']
                    if not zip_files:
                        continue
                    
                    start_date = min(zf['start_date'] for zf in zip_files)
                    end_date = max(zf['end_date'] for zf in zip_files)
                    
                    # Create output structure
                    date_range = f"{start_date}_{end_date}"
                    output_dir = os.path.join(date_range, server_id, "media")
                    screenshots_dir = os.path.join(output_dir, "screenshots")
                    videos_dir = os.path.join(output_dir, "video")
                    
                    os.makedirs(screenshots_dir, exist_ok=True)
                    os.makedirs(videos_dir, exist_ok=True)
                    
                    excel_data = []
                    temp_dirs_to_cleanup = []
                    
                    # Group covered events by ZIP file to minimize extractions
                    events_by_zip = report['events_by_zip']
                    
                    # Process each ZIP file
                    for zip_filename, events_in_zip in events_by_zip.items():
                        print(f"📦 Processing ZIP: {zip_filename} ({len(events_in_zip)} events)")
                        
                        # Find ZIP info
                        zip_info = next(z for z in zip_files if z['filename'] == zip_filename)
                        
                        # Extract ZIP
                        media_dir, temp_dir = self.extract_and_process_zip(zip_info, temp_base_dir)
                        temp_dirs_to_cleanup.append(temp_dir)
                        
                        if not media_dir:
                            print(f"❌ Could not extract media from {zip_filename}")
                            continue
                        
                        # Process events from this ZIP
                        for event in events_in_zip:
                            # Use the ZIP-specific media index instead of global index
                            zip_media_index = event['zip_media_index']
                            media_folder = os.path.join(media_dir, str(zip_media_index))
                            
                            if not os.path.exists(media_folder):
                                print(f"❌ Media folder {zip_media_index} not found in {zip_filename}")
                                continue
                            
                            # Find video file
                            video_file = None
                            for file in os.listdir(media_folder):
                                if file.endswith('.mkv'):
                                    video_file = os.path.join(media_folder, file)
                                    break
                            
                            if not video_file:
                                print(f"❌ No video found in media folder {zip_media_index}")
                                continue
                            
                            # Generate filenames
                            name = event.get('Name', '')
                            description = event.get('Description', '')
                            datetime_str = event.get('Date/Time', '')
                            
                            dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
                            formatted_datetime = dt.strftime("%Y-%m-%d-%H-%M-%S")
                            
                            screenshot_name = f"{name}_{description}_{formatted_datetime}.png"
                            screenshot_path = os.path.join(screenshots_dir, screenshot_name)
                            
                            # Extract screenshot
                            print(f"📸 Extracting screenshot: {name} (ZIP media index: {zip_media_index})")
                            success = extract_screenshot(video_file, screenshot_path, self.screenshot_timestamp)
                            
                            if success:
                                # Copy video
                                video_name = f"{name}_{description}_{formatted_datetime}.mkv"
                                video_output_path = os.path.join(videos_dir, video_name)
                                shutil.copy2(video_file, video_output_path)
                                
                                # Add to Excel data with relative path
                                excel_row = {
                                    'Name': name,
                                    'Description': description,
                                    'Date/Time': dt.strftime("%d/%m/%Y %H:%M"),
                                    'End Date/Time': datetime.strptime(event.get('End Date/Time', ''), "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M") if event.get('End Date/Time') else '',
                                    'True Event': '',
                                    'Data Intervento': '',
                                    'Attività svolta': '',
                                    'Screenshot': os.path.join(server_id, "media", "screenshots", screenshot_name).replace('\\', '/')  # Proper relative path
                                }
                                excel_data.append(excel_row)
                    
                    # Create Excel file
                    if excel_data:
                        excel_path = os.path.join(date_range, f"{server_id}_events_report.xlsx")
                        self.create_excel_with_links(excel_data, excel_path)
                        print(f"📊 Excel file created: {excel_path}")
                    
                    # Cleanup temporary directories for this server
                    for temp_dir in temp_dirs_to_cleanup:
                        if os.path.exists(temp_dir):
                            shutil.rmtree(temp_dir)
            
            except Exception as e:
                print(f"❌ An error occurred during processing: {e}")
                import traceback
                traceback.print_exc()
            
            finally:
                # Cleanup main temp directory
                if os.path.exists(temp_base_dir):
                    shutil.rmtree(temp_base_dir)
        
        print("\n✅ Processing completed!")
        return True

def main():
    processor = MultiServerEventProcessor(screenshot_timestamp=13)
    
    # Default to data directory
    default_directory = "data"
    
    # Check if data directory exists
    if not os.path.exists(default_directory):
        print(f"Creating data directory: {default_directory}")
        os.makedirs(default_directory)
        print("Please place your CSV and ZIP files in the 'data' directory and run again.")
        return
    
    directory = input(f"Enter directory path (or press Enter to use '{default_directory}'): ").strip()
    if not directory:
        directory = default_directory
    
    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        return
    
    processor.process_multiple_servers(directory)

if __name__ == "__main__":
    main()
