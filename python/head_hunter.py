import asyncio
import pandas as pd
from excel import get_vacancy_list, save_excel
from aiohttp import ClientSession
from fake_useragent import UserAgent
from utils import get_mediana

URL = 'https://api.hh.ru/vacancies'
COUNT = 100
DATA = {}


async def get_vacancy(vacancy_name: str):
    ua = UserAgent()
    headers = {
        "accept": "application/json",
        "User-Agent": ua.random
    }
    async with ClientSession(headers=headers) as session:
        response = await session.get(URL, data={
            'text': vacancy_name,
            'per_page': 100,
            'area': 113,
            'currency': 'RUR',
            'no_magic': True
        })

        return_data = []
        mediana = []
        data: dict = await response.json()
        for card in data['items']:
            return_card = {'Название': card['name']}
            if card['salary'] is None:
                return_card['Зарплата(От)'] = "Не указано"
                return_card['Зарплата(До)'] = "Не указано"
                return_card['Зарплата(Средняя)'] = "Не указано"
            else:
                if card['salary']['from'] is None:
                    return_card['Зарплата(От)'] = "Не указано"
                    return_card['Зарплата(До)'] = card['salary']['to']
                    return_card['Зарплата(Средняя)'] = "Не указано"
                    mediana.append(card['salary']['to'])
                elif card['salary']['to'] is None:
                    return_card['Зарплата(От)'] = card['salary']['from']
                    return_card['Зарплата(До)'] = "Не указано"
                    return_card['Зарплата(Средняя)'] = "Не указано"
                    mediana.append(card['salary']['from'])
                else:
                    return_card['Зарплата(От)'] = card['salary']['from']
                    return_card['Зарплата(До)'] = card['salary']['to']
                    return_card['Зарплата(Средняя)'] = (card['salary']['from'] + card['salary']['to']) / 2
                    mediana.append(return_card['Зарплата(Средняя)'])
            return_card['График'] = ''
            return_card['Ссылка'] = card['alternate_url']
            return_data.append(return_card)

    df = pd.DataFrame(return_data, index=None)
    if len(df) > 0:
        df['Медиана'] = get_mediana(mediana)
    else:
        df = pd.DataFrame(columns=list(DATA.values()))
    vacancy_name = vacancy_name[:30] if len(vacancy_name) > 30 else vacancy_name
    DATA[vacancy_name] = df


async def _collect_task(keys_path):
    tasks = []
    for vacancy_name in get_vacancy_list(keys_path):
        tasks.append(asyncio.create_task(get_vacancy(vacancy_name)))
    await asyncio.gather(*tasks)


async def async_collect_data(save_path: str, keys_path: str, count: int):
    global COUNT
    COUNT = count
    await _collect_task(keys_path)
    save_excel(DATA, save_path)
