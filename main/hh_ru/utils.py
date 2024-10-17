import requests
import re
import pandas as pd
import numpy as np


def save_excel(data: dict, path: str):
    with pd.ExcelWriter(path) as writer:
        for vacancy_name in sorted(data):
            data[vacancy_name].to_excel(writer, vacancy_name, index=False)


def get_mediana(med):
    n = len(med)
    index = n // 2
    if n % 2:
        return sorted(med)[index]
    return sum(sorted(med)[index - 1:index + 1]) / 2


def find_schedule(text):
    result = []
    html = text.lower()
    for i in range(0, 10):
        for j in range(0, 10):
            schedule = _find_schedule(f'{i}/{j}', html)
            if schedule is not None: result.append(schedule)
            schedule = _find_schedule(f'{i}\\{j}', html)
            if schedule is not None: result.append(schedule)
    return ', '.join(set(result)) if result else "Не указано"


def _find_schedule(schedule: str, text: str):
    try:
        _res = []
        for i in re.finditer(schedule, text):
            index = i.start()
            _schedule = str(schedule)
            _left_i = int(index)
            _right_i = int(index) + len(schedule)
            while True:
                try:
                    _left_i -= 1
                    _schedule = f'{int(text[_left_i])}{_schedule}'
                except ValueError:
                    break
                except IndexError:
                    break
            while True:
                try:
                    _schedule = f'{_schedule}{int(text[_right_i])}'
                    _right_i += 1
                except ValueError:
                    break
                except IndexError:
                    break
            _res.append(_schedule)
        return ', '.join(set(_res)) if _res else None
    except re.error:
        return None

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
    
    response = requests.get(url)
    _json = response.json()
    _find(_json)
    return locations

def get_text():
    return ["Повар холодного цеха",
    "Повар горячего цеха",
    "Повар универсал",
    "Подсобный рабочий",
    "Разнорабочий",
    "Комплектовщик",
    "Уборщик",
    "Швея",
    "Оператор линии производства",
    "Слесарь",
    "Сварщик",
    "Электромонтажники",
    "Сортировщики",
    "Горничные",
    "Дворники",
    "Обработчик",
    "Грузчик",
    "Водитель погрузчика",
    "Фасовщики",
    "Укладчики-упаковщики",
    "Мойщики",
    "Арматурщики",
    "Монтажники",
    "Формовщики",
    "Грохотовщик",
    "Дробильщик",
    "Водитель карьерного самосвала (БелАЗ)",
    "Машинист Экскаватора",
    "Водитель автопогрузчика",
    "Кладовщик",
    "Пекарь-формовщик",
    "Тестодел",
    "Техники",
    "Электрики",
    "Сантехники",
    "Стропальщики",
    "Электромонтажники",
    "Грузчик-прессовщик",
    "Кассир",
    "Курьер",
    "Токарь",
    "Фрезеровщик",
    "Монолитчики",
    "Строители",
    "Бетонщики",
    "Рабочий по обслуживанию зданий",
    "Прессовщик",
    "Станочник-распиловщик",
    "Водитель электроштабелера",
    "Обработчики",
    "Кондитер",
    "Механик",
    "Деревообработчики",
    "Раскройщики",
    "Мебельщики",
    "Обивщики мягкой мебели"]


def df_style(df: pd.DataFrame, condition=None):
    if not condition:
        condition = lambda col: col.index % 2 
    css_alt_rows = 'background-color: powderblue; color: black; text-align: center; border: 1px solid black;'
    css_indexes = 'background-color: steelblue; color: white; text-align: center; border: 1px solid black;'
    text_center = 'text-align: center; border: 1px solid black;'
    return (df.style.apply(lambda col: np.where(condition(col), css_alt_rows, text_center)) # alternating rows
        .applymap_index(lambda _: css_indexes, axis=0) # row indexes (pandas 1.4.0+)
        .applymap_index(lambda _: css_indexes, axis=1) # col indexes (pandas 1.4.0+)
    )