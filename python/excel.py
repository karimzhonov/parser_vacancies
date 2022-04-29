import pandas as pd

CONFIG_XLSX = '../search_keys.xlsx'

def get_vacancy_list(path):
    df = pd.DataFrame(pd.read_excel(path, 'Лист1', header=None)).reset_index(drop=True)
    return [row.strip('.') for row in df[0].iloc]


def save_excel(data: dict, path: str):
    writer = pd.ExcelWriter(path)
    for vacancy_name in sorted(data):
        data[vacancy_name].to_excel(writer, vacancy_name, index=False)
    writer.save()
