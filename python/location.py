import requests
import pandas as pd
from utils import get_headers
from excel import save_excel, get_vacancy_list


def get_hh_locations():
    """Get Location id"""
    locations = []

    def _find(data):
        """Recurent find id"""
        for area in data:
            locations.append({
                'location': area['name'],
                'hh_code': area['id']
            })
            if len(area['areas']) > 0:
                _find(area['areas'])

    url = f'https://api.hh.ru/areas'

    response = requests.get(url, headers=get_headers())
    _json = response.json()
    _find(_json)
    return locations


def main():
    keys_path = '../search_keys.xlsx'
    data = get_vacancy_list(keys_path)
    df = pd.DataFrame(get_hh_locations())
    save_excel({'1.Main': data, '2.Locations': df}, keys_path)
