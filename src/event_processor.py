import os
import csv
import shutil
from datetime import datetime
from . import file_utils
from . import coverage_analyzer
from . import excel_report
from . import summary_generator
from .video_processing import extract_screenshot
from config import DATETIME_FORMATS, DEFAULT_SCREENSHOT_TIMESTAMP

class MultiServerEventProcessor:
    def __init__(self, screenshot_timestamp=DEFAULT_SCREENSHOT_TIMESTAMP):
        self.screenshot_timestamp = screenshot_timestamp
        self.event_categories_summary = {}  # Track categories across all servers
        self.all_excel_data = []  # Store all Excel data for merging
    
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
                server_id = file_utils.extract_server_from_sensor_name(sensor_name)
                
                if not server_id:
                    print(f"Warning: Could not extract server ID from sensor name: '{sensor_name}'")
                    continue
                
                # Debug first few rows
                if i < 3:
                    print(f"DEBUG: Row {i}: Sensor='{sensor_name}', Server='{server_id}'")
                
                # Parse datetime - try multiple formats
                datetime_str = row.get('Date/Time', '')
                event_datetime = self._parse_datetime(datetime_str)
                
                if event_datetime is None:
                    print(f"Warning: Could not parse datetime for row {i}: {datetime_str} - tried multiple formats")
                    continue
                
                row['datetime_obj'] = event_datetime
                
                # Initialize server group if not exists
                if server_id not in events_by_server:
                    events_by_server[server_id] = []
                
                # Store the clean sensor name and global index
                row['Name'] = sensor_name
                row['global_index'] = len(events_by_server[server_id])  # Global index for this server
                
                # Debug: Print True Event value for first few rows
                if i < 3:
                    print(f"DEBUG: True Event in CSV: '{row.get('True Event', 'NOT_FOUND')}'")
                    print(f"DEBUG: All row keys: {list(row.keys())}")
                
                # Add to server group
                events_by_server[server_id].append(row)
        
        # Print summary
        for server_id, events in events_by_server.items():
            print(f"DEBUG: Server {server_id}: {len(events)} events")
        
        return events_by_server
    
    def _parse_datetime(self, datetime_str):
        """Parse datetime string with multiple possible formats."""
        for fmt in DATETIME_FORMATS:
            try:
                return datetime.strptime(datetime_str, fmt)
            except ValueError:
                continue
        return None
    
    def process_multiple_servers(self, directory):
        """Main processing function for multiple servers and ZIP files."""
        print("🔍 Scanning directory...")
        
        # Reset summary data for new processing
        self.event_categories_summary = {}
        self.all_excel_data = []
        
        # Scan directory
        zip_files_by_server, csv_files = file_utils.scan_directory(directory)
        
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
                coverage_reports[server_id] = coverage_analyzer.check_coverage_for_server(server_id, events, zip_files)
            
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
            
            # Store the date_range for merged report path
            merged_report_date_range = None
            
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
                    merged_report_date_range = date_range  # Store for merged report
                    output_dir = os.path.join(date_range, server_id)
                    screenshots_dir = os.path.join(output_dir, "screenshots")
                    videos_dir = os.path.join(output_dir, "video")
                    event_reports_dir = os.path.join(output_dir, "eventReports")
                    
                    os.makedirs(screenshots_dir, exist_ok=True)
                    os.makedirs(videos_dir, exist_ok=True)
                    os.makedirs(event_reports_dir, exist_ok=True)
                    
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
                        media_dir, temp_dir = file_utils.extract_and_process_zip(zip_info, temp_base_dir)
                        temp_dirs_to_cleanup.append(temp_dir)
                        
                        if not media_dir:
                            print(f"❌ Could not extract media from {zip_filename}")
                            continue
                        
                        # Process events from this ZIP
                        self._process_events_from_zip(
                            events_in_zip, media_dir, server_id, 
                            screenshots_dir, videos_dir, event_reports_dir, excel_data
                        )
                    
                    # Create individual server Excel file
                    if excel_data:
                        excel_path = os.path.join(date_range, f"{server_id}_events_report.xlsx")
                        # Remove 'Server' column for individual reports
                        individual_excel_data = [{k: v for k, v in row.items() if k != 'Server'} for row in excel_data]
                        excel_report.create_excel_with_links(individual_excel_data, excel_path)
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
        
        # Ask user if they want to create merged report
        if self.all_excel_data:
            print(f"\n📊 Individual server reports have been created.")
            print(f"Found {len(self.all_excel_data)} total events across all servers.")
            
            merge_response = input("Do you want to create a merged Excel report with all events? (y/n): ").strip().lower()
            if merge_response == 'y':
                self.create_merged_report(merged_report_date_range)
            else:
                print("⏭️  Skipping merged report creation.")
        
        # Display final summary
        summary_generator.display_final_summary(self.event_categories_summary)
        
        print("\n✅ Processing completed!")
        return True
    
    def _process_events_from_zip(self, events_in_zip, media_dir, server_id, 
                                screenshots_dir, videos_dir, event_reports_dir, excel_data):
        """Process events from a single ZIP file."""
        for event in events_in_zip:
            # Use the ZIP-specific media index instead of global index
            zip_media_index = event['zip_media_index']
            media_folder = os.path.join(media_dir, str(zip_media_index))
            
            if not os.path.exists(media_folder):
                print(f"❌ Media folder {zip_media_index} not found")
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
            
            # Track event categories
            if description not in self.event_categories_summary:
                self.event_categories_summary[description] = {'count': 0, 'servers': set()}
            self.event_categories_summary[description]['count'] += 1
            self.event_categories_summary[description]['servers'].add(server_id)
            
            # Use the already parsed datetime object instead of reparsing
            dt = event['datetime_obj']  # This was already parsed in read_and_group_events_by_server
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
                
                # Copy event snapshot if it exists
                snapshot_source = os.path.join(media_folder, "eventSnapshot.jpg")
                if os.path.exists(snapshot_source):
                    snapshot_name = f"{name}_{description}_{formatted_datetime}_eventSnapshot.jpg"
                    snapshot_output_path = os.path.join(event_reports_dir, snapshot_name)
                    shutil.copy2(snapshot_source, snapshot_output_path)
                    print(f"📷 Copied event snapshot: {snapshot_name}")
                else:
                    print(f"⚠️  Event snapshot not found for: {name} (media folder {zip_media_index})")
                
                # Parse End Date/Time with multiple formats
                end_datetime_str = event.get('End Date/Time', '')
                formatted_end_datetime = self._format_end_datetime(end_datetime_str)
                
                # Add to Excel data with relative path
                true_event_value = event.get('True Event', '')
                
                # Debug: Print True Event value being added to Excel
                if len(excel_data) < 3:  # Only for first few events
                    print(f"DEBUG: True Event value being added to Excel: '{true_event_value}'")
                    print(f"DEBUG: Available keys in event: {list(event.keys())}")
                
                excel_row = {
                    'Server': server_id,  # Add server column for merged report
                    'Name': name,
                    'Description': description,
                    'Date/Time': dt.strftime("%d/%m/%Y %H:%M"),
                    'End Date/Time': formatted_end_datetime,
                    'True Event': true_event_value,  # Copy True Event from input CSV
                    'Data Intervento': '',
                    'Attività svolta': '',
                    'Screenshot': os.path.join(server_id, "screenshots", screenshot_name).replace('\\', '/')  # Updated relative path
                }
                excel_data.append(excel_row)
                
                # Add to global data for merged report
                merged_excel_row = excel_row.copy()
                merged_excel_row['Screenshot'] = os.path.join(server_id, "screenshots", screenshot_name).replace('\\', '/')
                self.all_excel_data.append(merged_excel_row)
    
    def _format_end_datetime(self, end_datetime_str):
        """Format end datetime from event data."""
        formatted_end_datetime = '-'
        
        if end_datetime_str and end_datetime_str != '-':
            for fmt in DATETIME_FORMATS:
                try:
                    end_dt = datetime.strptime(end_datetime_str, fmt)
                    formatted_end_datetime = end_dt.strftime("%d/%m/%Y %H:%M")
                    break
                except ValueError:
                    continue
        
        return formatted_end_datetime
    
    def create_merged_report(self, date_range_dir):
        """Create a merged Excel report with all events from all servers."""
        if not self.all_excel_data:
            print("⚠️  No data to merge")
            return
        
        # Sort by date/time for better readability
        self.all_excel_data.sort(key=lambda x: datetime.strptime(x['Date/Time'], "%d/%m/%Y %H:%M"))
        
        # Create merged Excel file in the same date range directory as individual reports
        if date_range_dir:
            merged_excel_path = os.path.join(date_range_dir, "complete_events_report.xlsx")
        else:
            # Fallback to current directory if no date range available
            merged_excel_path = "complete_events_report.xlsx"
        
        excel_report.create_excel_with_links(self.all_excel_data, merged_excel_path)
        
        print(f"\n📊 Merged report created: {merged_excel_path}")
        print(f"   Total events: {len(self.all_excel_data)}")
