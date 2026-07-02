import openpyxl

def remove_sheet_protection(input_file, output_file):
    # openpyxl strips the underlying sheet protection hash when saving
    wb = openpyxl.load_workbook(input_file)
    
    for sheet in wb.worksheets:
        sheet.protection.disable() # Disables the editing lock
        
    wb.save(output_file)
    print(f"Success! Editing restrictions removed. Saved as: {output_file}")

# Example Usage
remove_sheet_protection(r"/Users/tom/Documents/interest-rate-swap-pricer-v10/swap-pricer-v10-o365.xlsm", "swap-pricer-v10-o365.xlsm")
