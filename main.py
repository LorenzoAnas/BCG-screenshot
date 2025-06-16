import os
from src.event_processor import MultiServerEventProcessor

def main():
    processor = MultiServerEventProcessor()
    
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
