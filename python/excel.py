import warnings
import json
import os
import os.path
import httplib2
import pandas as pd
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

warnings.simplefilter("ignore")

CONFIG_XLSX = os.path.join(os.path.dirname(__file__), '../search_keys.xlsx')


def get_vacancy_list(path=CONFIG_XLSX):
    data = pd.read_excel(path, '1.Main')
    return pd.DataFrame(data, columns=data.columns.values)


def save_excel(data: dict, path: str):
    writer = pd.ExcelWriter(path)
    for vacancy_name in sorted(data):
        data[vacancy_name].to_excel(writer, vacancy_name, index=False)
    writer.save()


def get_service_sacc():
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds_json = os.path.join(os.path.dirname(__file__), '../auth.json')

    creds_service = ServiceAccountCredentials.from_json_keyfile_name(creds_json, scopes).authorize(httplib2.Http())
    return build('sheets', 'v4', http=creds_service)


def get_sheet():
    config_path = os.path.join(os.path.dirname(__file__), '../config.json')
    sheet_id = json.load(open(config_path))['sheet_id']
    resp = get_service_sacc().spreadsheets().values().get(spreadsheetId=sheet_id, range="A1:G100").execute()
    keys = resp['values'][0]
    data = []
    for row in resp['values'][1:]:
        vacancy = {}
        for key, value in zip(keys, row):
            if 'Дата' in key:
                value_list = value.split('/')[::-1]
                value_list[0] = f'20{value_list[0]}'
                value = '-'.join(value_list)
            vacancy[key] = value.replace('.', '')
        data.append(vacancy)
    return data
