import pandas as pd
import os

def create_excel_with_links(data, output_path):
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
