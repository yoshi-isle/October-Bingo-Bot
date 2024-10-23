import gspread
from gspread_formatting import *
import json

class UserSheetsService:
    def __init__(self, config_path, key_path):
        self.config_path = config_path
        self.key_path = key_path
        self.client = self.authorize_client()

    def authorize_client(self):
        try:
            return gspread.service_account(self.key_path)
        except Exception as e:
            print(f"Error connecting: {e}")
            return None

    def create_sheet(self, sheet_name):
        if self.client is None:
            return {"error": "Error connecting to Google Sheets"}, 500

        if not sheet_name:
            return {"error": "Sheet name is required"}, 400

        try:
            new_sheet = self.client.create(sheet_name)
            config = self.load_config()
            new_sheet.share(config['gmail'], 'user', 'writer')
            new_sheet.share(None, 'anyone', 'reader')

            pawWorksheet = new_sheet.get_worksheet(0)
            pawWorksheet.update_title("Submissions")
            pawWorksheet.update_cell(1, 1, f"{sheet_name}'s bingo submission history")
            set_column_width(pawWorksheet, 'A', 240)

            fmt = cellFormat(
                textFormat=textFormat(bold=True),
                horizontalAlignment='CENTER'
            )
            format_cell_range(pawWorksheet, 'A1:C1', fmt)

            # Add formula for summing points in column C
            pawWorksheet.update_cell(1, 2, "Total Points:")
            pawWorksheet.update_cell(1, 3, '=SUM(C2:C)')

            return new_sheet.url
        except Exception as e:
            return {"error": f"Error adding sheet: {e}"}, 500

    def add_submission(self, sheet_url, name, drop_name, points, image_url):
        if self.client is None:
            return {"error": "Error connecting to Google Sheets"}, 500
        
        try:
            # Open the sheet using the URL
            sheet = self.client.open_by_url(sheet_url)
            pawWorksheet = sheet.get_worksheet(0)
            
            # Find the next empty row (based on column A)
            next_row = len(pawWorksheet.col_values(1)) + 1
            
            # Insert the new data into the next row as a list of lists
            pawWorksheet.update(f"A{next_row}:D{next_row}", [[name, drop_name, points, image_url]])
            
            return {"message": "Submission added successfully"}, 200
        except Exception as e:
            return {"error": f"Error adding submission: {e}"}, 500




    def load_config(self):
        with open(self.config_path, 'r') as f:
            return json.load(f)
