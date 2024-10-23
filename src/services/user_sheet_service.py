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
            new_sheet.add_worksheet("Kitty PvM Diary", 30, 20)
            config = self.load_config()
            new_sheet.share(config['gmail'], 'user', 'writer')
            new_sheet.share(None, 'anyone', 'reader')

            pawWorksheet = new_sheet.get_worksheet(0)
            pawWorksheet.update_title("Paw Prints")
            pawWorksheet.update_cell(1,1,"yoshe's Clan Profile")
            set_column_width(pawWorksheet, 'A', 240)

            fmt = cellFormat(
                backgroundColor=color(1, 0.9, 0.9),
                textFormat=textFormat(bold=True, foregroundColor=color(1, 0, 1)),
                horizontalAlignment='CENTER'
            )
            format_cell_range(pawWorksheet, 'A1:B1', fmt)

            return new_sheet.url
        except Exception as e:
            return {"error": f"Error adding sheet: {e}"}, 500

    def get_sheet_by_username(self, username):
            if self.client is None:
                return {"error": "Error connecting to Google Sheets"}, 500

            try:
                sheet = self.client.open(f"{username}'s sheet")
                return {
                    "sheet": sheet.title,
                    "url": sheet.url
                }, 200
            except Exception as e:
                return {"error": f"Failed to get sheet for user {username}: {e}"}, 500
            
    def delete_sheet(self, name):
        if self.client is None:
            return {"error": "Error connecting to Google Sheets"}, 500

        try:
            for sheet in self.client.openall():
                self.client.del_spreadsheet(sheet.id)
            return {"sheet": name}, 200
        except Exception as e:
            return {"error": f"Failed to delete sheet: {e}"}, 500

    def load_config(self):
        with open(self.config_path, 'r') as f:
            return json.load(f)
