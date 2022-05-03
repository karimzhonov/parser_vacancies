import asyncio
import pandas as pd
from datetime import datetime
from aiohttp import ClientSession
from excel import get_vacancy_list, save_excel
from utils import get_mediana, get_headers
from schedule import find_schedule
from bs4 import BeautifulSoup

URL = 'https://api.hh.ru'
COUNT = 100
DATA = {}


async def get_location_id(name: str):
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
    """Get vacancies"""
    url = f'{URL}/vacancies'
    async with ClientSession(headers=get_headers()) as session:
        area = await get_location_id(vacancy['Локоция'])
        area = 113 if area is None else area
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
            return_card = {
                'Название': card['name'],
                'Зарплата(От)': "Не указано",
                'Зарплата(До)': "Не указано",
                'Зарплата(Средняя)': "Не указано",
            }
            if card['salary'] is not None:
                if card['salary']['from'] is not None:
                    return_card['Зарплата(От)'] = card['salary']['from']
                    mediana.append(card['salary']['from'])
                elif card['salary']['to'] is not None:
                    return_card['Зарплата(До)'] = card['salary']['to']
                    mediana.append(card['salary']['to'])
                else:
                    return_card['Зарплата(От)'] = card['salary']['from']
                    return_card['Зарплата(До)'] = card['salary']['to']
                    return_card['Зарплата(Средняя)'] = (card['salary']['from'] + card['salary']['to']) / 2
                    mediana.append(return_card['Зарплата(Средняя)'])
            # Scedule
            html_response = await session.get(card['alternate_url'], ssl=False)
            html = await html_response.text()
            soup = BeautifulSoup(html, features='lxml')
            desc = soup.find(attrs={'data-qa': "vacancy-description"})
            return_card['График'] = find_schedule(desc.text)
            return_card['Ссылка'] = card['alternate_url']
            return_data.append(return_card)
        df = pd.DataFrame(return_data, index=None)
        if len(df) > 0:
            df['Медиана'] = get_mediana(mediana)
        else:
            df = pd.DataFrame(columns=list(DATA.values()))
        vacancy_name = vacancy['Ключи'][:30] if len(vacancy['Ключи']) > 30 else vacancy['Ключи']
        df = df.sort_values(['График'])
        DATA[vacancy_name] = df
        print(f'Parsed vacancy: {vacancy_name}')


async def async_collect_data(save_path: str, keys_path: str, async_tasks_count: int = 3):
    t0 = datetime.now()
    counter = 0
    tasks = []
    for vacancy in get_vacancy_list(keys_path).iloc:
        counter += 1
        tasks.append(asyncio.create_task(get_vacancy(vacancy)))
        if counter >= async_tasks_count:
            await asyncio.gather(*tasks)
            counter = 0
            tasks = []
    if len(tasks) > 0:
        await asyncio.gather(*tasks)
    save_excel(DATA, save_path)
    print(f'Wasted time: {datetime.now() - t0}')
