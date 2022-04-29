import pandas as pd

CONFIG_XLSX = '../search_keys.xlsx'

def get_vacancy_list(path):
    data = pd.read_excel(path, 'Лист1')
    return pd.DataFrame(data, columns=data.columns.values)


def save_excel(data: dict, path: str):
    writer = pd.ExcelWriter(path)
    for vacancy_name in sorted(data):
        data[vacancy_name].to_excel(writer, vacancy_name, index=False)
    writer.save()
