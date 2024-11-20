import requests
import pandas as pd
import io
from fastapi import HTTPException
from .utils import get_mediana, df_style


def get_vacancy(text, data, url=f'https://api.hh.ru/vacancies'):
    try:
        response = requests.get(url, params={'text': f"!{text}", "search_field": "name", **data})
    except Exception as _exp:
        print(_exp)
        return None
    if response.status_code != 200:
        print(response.json())
        return None
    data: dict = response.json()
    return_data = []
    mediana = []
    if not data.get("items"):
        print(data)
        return None
    if len(data['items']):
        for card in data['items']:
            return_card = {
                'Название': card['name'],
                'Зарплата(От)': "Не указано",
                'Зарплата(До)': "Не указано",
                'Зарплата(Средняя)': "Не указано",
            }
            if card['salary'] is not None:
                if card['salary']['from'] is not None and card['salary']['to'] is None:
                    return_card['Зарплата(От)'] = card['salary']['from']
                    mediana.append(card['salary']['from'])
                elif card['salary']['to'] is not None and card['salary']['from'] is None:
                    return_card['Зарплата(До)'] = card['salary']['to']
                    mediana.append(card['salary']['to'])
                elif card['salary']['to'] is not None and card['salary']['from'] is not None:
                    return_card['Зарплата(От)'] = card['salary']['from']
                    return_card['Зарплата(До)'] = card['salary']['to']
                    mediana.append((card['salary']['from'] + card['salary']['to']) / 2)
            # Scedule
            return_card['Ссылка'] = card['alternate_url']
            # try:
            #     html_response = requests.get(card['alternate_url'])
            #     html = html_response.text
            #     soup = BeautifulSoup(html, features='lxml')
            #     return_card['График'] = find_schedule(soup.text)
            # except Exception as _exp:
            #     print(_exp)
            return_data.append(return_card)
        df = pd.DataFrame(return_data, index=None)
        if len(df) > 0 and len(mediana) > 0:
            df['Зарплата(Средняя)'] = round(sum(mediana) / len(mediana), 0)
            df['Медиана'] = get_mediana(mediana)
        df["Вакансия"] = text
        df["Ссылка"] = df.pop('Ссылка')
        # df = df.sort_values(['График'])
        return df
    return None
    
def collect_file(data):
    counter = 0
    dfs = []
    for text in data.text.split(","):
        counter += 1
        df = get_vacancy(text, {
            "area": data.area,
            "per_page": int(data.per_page) if int(data.per_page) <= 100 else 100,
            "date_from": data.date_from,
            "date_to": data.date_to,
            "currency": data.currency,
        })
        if df is None:
            continue
        dfs.append(df)
    if not dfs:
        raise HTTPException(status_code=404, detail="Ваканции не найденo")
    df = pd.concat(dfs)
    df.reset_index(inplace=True)
    df = df_style(df)
    output = io.BytesIO()
    writer = pd.ExcelWriter(output)
    df.to_excel(writer, index=False)
    writer.close()
    return output.getvalue()
