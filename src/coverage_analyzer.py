from datetime import timedelta

def check_coverage_for_server(server_id, events, zip_files):
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

# Alias for backward compatibility
def check_coverage(server_id, events, zip_files):
    """Alias for check_coverage_for_server function."""
    return check_coverage_for_server(server_id, events, zip_files)
