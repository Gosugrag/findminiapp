import os
import time
import logging
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

logger = logging.getLogger("google.sheet.manager")
timestamp = time.strftime("%Y%m%d_%H%M%S")


class GoogleSheetsManager:
    def __init__(self, spreadsheet_name=f"findminiapp-{timestamp}"):
        """Initialize Google Sheets client and open or create a spreadsheet."""
        self.spreadsheet_name = spreadsheet_name
        self.creds = self.authenticate_google_sheets()
        self.sheets_service = build("sheets", "v4", credentials=self.creds)
        self.drive_service = build("drive", "v3", credentials=self.creds)
        self.spreadsheet_id = self.create_spreadsheet()

    def authenticate_google_sheets(self):
        """Authenticate and return Google API credentials."""
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        return Credentials.from_service_account_file("credentials.json",
                                                     scopes=scope)

    def create_spreadsheet(self):
        """Check if spreadsheet exists, otherwise create it."""
        try:
            # Create a new spreadsheet
            spreadsheet = {
                "properties": {"title": self.spreadsheet_name}
            }
            response = self.sheets_service.spreadsheets().create(
                body=spreadsheet).execute()
            spreadsheet_id = response["spreadsheetId"]

            # Share with a user
            self.share_spreadsheet(spreadsheet_id, os.getenv('USER_EMAIL'))
            logger.info(
                f"✅ Created new spreadsheet: {self.spreadsheet_name}")

            return spreadsheet_id

        except Exception as e:
            logger.error(f"❌ Failed to create spreadsheet: {e}")
            return None

    def share_spreadsheet(self, spreadsheet_id, user_email):
        """Share spreadsheet with a user."""
        permission = {
            "type": "user",
            "role": "writer",
            "emailAddress": user_email,
            "pendingOwner": True
        }
        custom_message = f"Hello,\n\nI have shared a Google Spreadsheet with you. You can access it via the link below:\n\nhttps://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        self.drive_service.permissions().create(
            fileId=spreadsheet_id,
            body=permission,
            sendNotificationEmail=True,
            emailMessage=custom_message
        ).execute()

    def rename_first_sheet(self, row_nums):
        """Rename the first sheet if it's the default sheet."""
        try:
            body={
                "requests": [
                    {
                        "updateSheetProperties": {
                            "properties": {
                                "title": f"Data_{timestamp}"},
                            "fields": "title",
                        },
                    },
                ]
            }
            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id, body=body
            ).execute()
            self.update_dimenstion_properties(None, row_nums)
            return f"Data_{timestamp}"
        except Exception as e:
            logger.error(f"❌ Failed to rename first sheet: {e}")
            return None

    def update_dimenstion_properties(self, sheet_id, row_nums):
        update_dimensions_request = {
            "requests": [
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": sheet_id,
                            "gridProperties": {"rowCount": row_nums + 1}  # Ensure row count matches required rows
                        },
                        "fields": "gridProperties.rowCount"
                    }
                },
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "ROWS",
                            "startIndex": 1,
                            "endIndex": row_nums + 1
                        },
                        "properties": {"pixelSize": 200},
                        "fields": "pixelSize"
                    }
                },
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": 0,
                            "endIndex": 8
                        },
                        "properties": {"pixelSize": 400},
                        "fields": "pixelSize"
                    }
                },
                {
                    "updateCells": {
                        "range": {
                            "sheetId": sheet_id,
                            "startColumnIndex": 1,  # Column B (index 1)
                            "endColumnIndex": 2,  # Only Column B
                            "startRowIndex": 1,  # Start from row 2 (index 1)
                            "endRowIndex": row_nums + 1
                        },
                        "fields": "userEnteredFormat.wrapStrategy",
                        "rows": [
                            {
                                "values": [
                                    {
                                        "userEnteredFormat": {
                                            "wrapStrategy": "WRAP"
                                        }
                                    }
                                 ]
                            }
                        ] * row_nums,
                    }
                },
            ]
        }

        self.sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=self.spreadsheet_id, body=update_dimensions_request
        ).execute()

    def store_data(self, data):
        """Store data in the first sheet if it is empty, otherwise create a new sheet."""
        if not data:
            logger.warning("⚠️ No data to upload.")
            return
        try:
            # Get the first sheet's data to check if it's empty
            row_nums = len(data)
            logger.info(f"✔️ First sheet is empty. Storing data in it.")
            sheet_title = self.rename_first_sheet(row_nums)
            range_name = f"'{sheet_title}'!A1"

            header = ["Name", "Description", "Telegram App Link", "FindMiniApp Link",
                      "Category", "Number Of Users", "Language", "Useful Links",
                      "Images"]
            values = [header] + data
            body = {"values": values}

            # Write data to the sheet (replaces any existing data)
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                body=body,
            ).execute()
            logger.info("✅ Data successfully stored in Google Sheets!")

        except Exception as e:
            logger.error(f"❌ Failed to store data: {e}")
