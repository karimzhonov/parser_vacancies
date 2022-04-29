import asyncio
import pandas as pd
from excel import get_vacancy_list, save_excel
from aiohttp import ClientSession
from utils import get_mediana, get_headers

URL = 'https://api.hh.ru'
COUNT = 100
DATA = {}


async def get_location_id(name):
    """Get Location id"""

    def _find(data):
        """Recurent find id"""
        for area in data:
            if area['name'] == name:
                return area['id']
            else:
                if len(area) > 0:
                    _a = _find(area['areas'])
                    if _a is None:
                        continue
                    else:
                        return _a
                else:
                    continue

    url = f'{URL}/areas'
    async with ClientSession(headers=get_headers()) as session:
        response = await session.get(url)
        _json = await response.json()
        return _find(_json)


async def get_vacancy(vacancy):
    """
    Get vacancies
    @param vacancy: Series
    """
    url = f'{URL}/vacancies'
    area = await get_location_id(vacancy['Локоция'])
    area = 113 if area is None else area
    async with ClientSession(headers=get_headers()) as session:
        response = await session.get(url, data={
            'text': vacancy['Ключи'].strip('.'),
            'per_page': vacancy['Количество вакансии'],
            'area': area,
            'date_from': vacancy['Дата от'].date(),
            'date_to': vacancy['Дата до'].date(),
            'currency': 'RUR',
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
    vacancy_name = vacancy['Ключи'][:30] if len(vacancy['Ключи']) > 30 else vacancy['Ключи']
    DATA[vacancy_name] = df


async def _collect_task(keys_path):
    tasks = []
    for vacancy in get_vacancy_list(keys_path).iloc:
        tasks.append(asyncio.create_task(get_vacancy(vacancy)))
    await asyncio.gather(*tasks)


async def async_collect_data(save_path: str, keys_path: str):
    await _collect_task(keys_path)
    save_excel(DATA, save_path)
