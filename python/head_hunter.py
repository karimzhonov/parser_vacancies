import asyncio
import pandas as pd
from datetime import datetime
from aiohttp import ClientSession
from excel import save_excel, get_sheet
from utils import get_mediana, get_headers
from schedule import find_schedule
from location import get_hh_locations
from bs4 import BeautifulSoup

URL = 'https://api.hh.ru'
COUNT = 100
DATA = {}
LOCATIONS: list[dict] = ...


async def get_vacancy(vacancy):
    """Get vacancies"""
    try:
        url = f'{URL}/vacancies'
        async with ClientSession(headers=get_headers()) as session:
            # Set location
            area = None
            for loc in LOCATIONS:
                if vacancy['Локоция'] == loc['location']:
                    area = loc['hh_code']
                    break
            area = 113 if area is None else area
            response = await session.get(url, data={
                'text': vacancy['Ключи'].strip('.'),
                'per_page': vacancy['Количество вакансии'],
                'area': area,
                'date_from': vacancy['Дата от'],
                'date_to': vacancy['Дата до'],
                'currency': 'RUR',
            })

            return_data = []
            mediana = []
            data: dict = await response.json()
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
                            return_card['Зарплата(Средняя)'] = card['salary']['from']
                            mediana.append(card['salary']['from'])
                        elif card['salary']['to'] is not None and card['salary']['from'] is None:
                            return_card['Зарплата(До)'] = card['salary']['to']
                            return_card['Зарплата(Средняя)'] = card['salary']['to']
                            mediana.append(card['salary']['to'])
                        elif card['salary']['to'] is not None and card['salary']['from'] is not None:
                            return_card['Зарплата(От)'] = card['salary']['from']
                            return_card['Зарплата(До)'] = card['salary']['to']
                            return_card['Зарплата(Средняя)'] = (card['salary']['from'] + card['salary']['to']) / 2
                            mediana.append(return_card['Зарплата(Средняя)'])
                    # Scedule
                    html_response = await session.get(card['alternate_url'], ssl=False)
                    html = await html_response.text()
                    soup = BeautifulSoup(html, features='lxml')
                    return_card['График'] = find_schedule(soup.text)
                    return_card['Ссылка'] = card['alternate_url']
                    return_data.append(return_card)
                df = pd.DataFrame(return_data, index=None)
                if len(df) > 0:
                    df['Медиана'] = get_mediana(mediana)
                else:
                    df = pd.DataFrame(columns=list(DATA.values()))
                vacancy_name = vacancy['Ключи'][:30] if len(vacancy['Ключи']) > 30 else vacancy['Ключи']
                vacancy_name = vacancy_name.replace('.', '')
                df = df.sort_values(['График'])
                DATA[vacancy_name] = df
                print(f'Parsed vacancy: {vacancy_name}')
    except Exception as _exp:
        print(_exp)


async def async_collect_data(save_path: str, async_tasks_count: int = 2):
    global LOCATIONS
    LOCATIONS = get_hh_locations()
    t0 = datetime.now()
    counter = 0
    tasks = []
    for vacancy in get_sheet():
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
