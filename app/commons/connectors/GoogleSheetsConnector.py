import os
from enum import Enum

import httplib2
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient import discovery


class ResultMode(Enum):
    FLAT = 1
    ZIP = 2
    RAW = 3


# TODO validar que se respete el orden de los rangos
def flatten(values):
    f = lambda l: sum(map(f, l), []) if isinstance(l, list) else [l]
    return f(values)


def zipped(values):
    return list(zip(*values))


def raw(values):
    return values


class GoogleSheetsConnector:

    scopes = ['https://www.googleapis.com/auth/spreadsheets']

    def __init__(self, app):

        self.logger = app.logger
        self.config = app.config
        self.service = None

    def authenticate(self):
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir, self.config.get("drive", "credentials"))
        credentials = ServiceAccountCredentials.from_json_keyfile_name(credential_path, self.scopes)
        discovery_url = self.config.get("drive", "sheets.discovery_url")
        self.logger.debug("GoogleSheetsConnector - Authorizing")
        self.service = discovery.build('sheets', 'v4',
                                       http=credentials.authorize(httplib2.Http()),
                                       discoveryServiceUrl=discovery_url)

    def format_results(self, values, mode):
        if mode == ResultMode.FLAT:
            return flatten(values)
        elif mode == ResultMode.ZIP:
            return zipped(values)
        else:
            return raw(values)

    def sheet_meta_data(self, spreadsheet_id):
        self.authenticate()
        return self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute().get('sheets', '')

    def single_range_fetch(self, spreadsheet_id, the_range, result_mode=ResultMode.FLAT):
        self.authenticate()
        self.logger.debug("GoogleSheetsConnector - Reading from %s" % the_range)
        values = self.service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=the_range).execute().get('values', [])
        return self.format_results(values, result_mode)

    # spreadsheet: string
    # ranges: [string]
    # result_mode: enum (FLAT, ZIP, RAW)
    def multi_range_fetch(self, spreadsheet_id, ranges, result_mode=ResultMode.FLAT):
        self.authenticate()
        self.logger.debug("GoogleSheetsConnector - Reading from %s" % ranges)
        value_ranges = self.service.spreadsheets().values().batchGet(
            spreadsheetId=spreadsheet_id, ranges=ranges).execute().get('valueRanges', [])

        values = [flatten(v.get('values', [])) for v in value_ranges]
        return self.format_results(values, result_mode)

    # For each (row) @range on the @spreadsheet, it writes a row of @values
    # spreadsheet: string
    # ranges: [string]
    # values: [[string]]
    def write(self, spreadsheet_id, ranges, values=[[]]):
        self.authenticate()
        value_ranges = []
        i = 0
        for r in ranges:
            value_ranges.append({"range": r, "majorDimension": "ROWS", "values": values[i]})
            i += 1
        body = {"data": value_ranges, "includeValuesInResponse": False, "valueInputOption": "RAW"}
        self.logger.debug("GoogleSheetsConnector - Writing to %s" % ranges)
        return self.service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id, body=body).execute()

    def write2(self, spreadsheet_id, ranges, values=[[]]):
        self.authenticate()
        data = [
            {
                'range' : ranges,
                'values' : values
            }
        ]
        body = {"data": data, "valueInputOption": "RAW"}
        self.logger.info("GoogleSheetsConnector - Writing to %s" % ranges)
        return self.service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id, body=body).execute()

    def clean_sheet(self, spreadsheet_id, sheet_id, hasTitles=False, title_row_count=1):
        meta = self.sheet_meta_data(spreadsheet_id)
        self.logger.info("Cleaning '" + sheet_id)
        start_col = end_col = start_row = end_row = 1
        if hasTitles:
            start_row = title_row_count + 1
        for prop in meta:
            if prop["properties"]["title"] == sheet_id:
                end_col = prop["properties"]["gridProperties"]["columnCount"]
                end_row = prop["properties"]["gridProperties"]["rowCount"]
        row = ['' for i in range(start_col, end_col + 1)]
        ranges = [sheet_id + "!%s:%s" % (n, n) for n in range(start_row, end_row + 1)]
        values = [[row] for i in ranges]
        self.write(spreadsheet_id, ranges, values)

    def single_row(self, spreadsheet_id, range, values=[[]], mode="update", value_input="RAW"):
        self.authenticate()
        body = {"values" : values}
        self.logger.debug("GoogleSheetsConnector - Updating sheet")
        if(mode == "append"):
            return self.service.spreadsheets().values().append(spreadsheetId=spreadsheet_id, range=range, valueInputOption=value_input, body=body).execute()
        else:
            return self.service.spreadsheets().values().update(spreadsheetId=spreadsheet_id, range=range, valueInputOption=value_input, body=body).execute()
