import re
import time
import pandas as pd
from tqdm import tqdm
from threading import Thread
from datetime import datetime
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from schedule import find_schedule
from excel import save_excel, get_sheet
from utils import get_driver, get_mediana

DATA = {}
URL = f'https://www.avito.ru/rossiya/vakansii'


def find_element(driver, by, value, delay=10, *, rec=0) -> WebElement:
    try:
        return WebDriverWait(driver, delay).until(EC.presence_of_element_located((by, value)))
    except TimeoutException as _exp:
        print(f'[TimeoutExp] {driver.current_url} - {by}: {value}')
        if rec >= 1: raise WebDriverException(_exp.msg)
        driver.refresh()
        return find_element(driver, by, value, delay, rec=rec + 1)


def find_elements(driver, by, value, delay=10, *, rec=0) -> list[WebElement]:
    try:
        return WebDriverWait(driver, delay).until(EC.presence_of_all_elements_located((by, value)))
    except TimeoutException as _exp:
        print(f'[TimeoutExp] {driver.current_url} - {by}: {value}')
        if rec >= 1: raise WebDriverException(_exp.msg)
        driver.refresh()
        return find_elements(driver, by, value, delay, rec=rec + 1)


def get_vacancy_data(driver, mediana):
    return_card = {
        'Название': "Не указано",
        'Зарплата(От)': "Не указано",
        'Зарплата(До)': "Не указано",
        'Зарплата(Средняя)': "Не указано",
        'График': "Не указано",
        'Ссылка': "Не указано",
    }
    try:
        soup = BeautifulSoup(driver.page_source, features='lxml')
        desc = soup.find('div', class_='item-view-main').text
        return_card['График'] = find_schedule(desc)
        return_card['Ссылка'] = driver.current_url
        return_card['Название'] = soup.find(class_='title-info-main').text
        price = soup.find('span', attrs={'itemprop': 'price'}).text.lower()
        price = str(price).replace(' ', '').replace(u'\xa0', '')
        if 'от' in price:
            price = price.replace('от', '')
            return_card['Зарплата(От)'] = float(price)
            mediana.append(float(price))
        elif 'до' in price:
            price = price.replace('до', '')
            return_card['Зарплата(До)'] = float(price)
            mediana.append(float(price))
        elif '—' in price:
            from_p, to_p = price.split('—')
            return_card['Зарплата(От)'] = float(from_p)
            return_card['Зарплата(До)'] = float(to_p)
            return_card['Зарплата(Средняя)'] = (return_card['Зарплата(От)'] + return_card['Зарплата(До)']) / 2
            mediana.append(return_card['Зарплата(Средняя)'])
            return return_card
    except Exception as _exp:
        print(_exp)


def collect_vacancy(driver, items, text, mediana):
    vac_data = []
    for item in tqdm(items, desc=f'Parsing vacancy: {text} - '):
        item.click()
        time.sleep(1)
        driver.switch_to.window(driver.window_handles[1])
        data = get_vacancy_data(driver, mediana)
        if data is not None: vac_data.append(data)
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
    return vac_data


def get_vacancy_page(driver, vacancy, data):
    try:
        mediana = []
        text = vacancy['Ключи'].strip('.')
        count = int(vacancy['Количество вакансии'])
        location = re.sub(r'\([^()]*\)', '', vacancy['Локоция'])
        url = f'{URL}?q={text}'
        driver.delete_all_cookies()
        driver.get(url)
        find_element(driver, By.XPATH, '//div[@data-marker="search-form/region"]').click()
        location_window = find_element(driver, By.XPATH, '//div[@data-marker="popup-location/overlay"]')
        location_window.find_element(By.XPATH, '//input[@data-marker="popup-location/region/input"]').send_keys(
            location)
        time.sleep(1)
        location_window.find_element(By.XPATH, '//ul[@data-marker="suggest-list"]') \
            .find_elements(By.TAG_NAME, 'li')[0].click()
        location_window.find_element(By.XPATH, '//button[@data-marker="popup-location/save-button"]').click()
        vac_data = []
        while True:
            items = find_elements(driver, By.XPATH, '//div[@data-marker="item"]')
            if len(items) >= count:
                vac_data = [*vac_data, *collect_vacancy(driver, items[:count], text, mediana)]
                break
            else:
                count -= len(items)
                vac_data = [*vac_data, *collect_vacancy(driver, items, text, mediana)]
                try:
                    driver.find_element(By.XPATH, '//span[@data-marker="pagination-button/next"]').click()
                except WebDriverException:
                    break
        df = pd.DataFrame(vac_data, index=None)
        if len(df) > 0:
            df['Медиана'] = get_mediana(mediana)
        else:
            df = pd.DataFrame(columns=list(DATA.values()))
        vacancy_name = vacancy['Ключи'][:30] if len(vacancy['Ключи']) > 30 else vacancy['Ключи']
        vacancy_name = vacancy_name.replace('.', '')
        df = df.sort_values(['График'])
        print(f'Parsed vacancy: {vacancy_name}')
        data[vacancy_name] = df
    except Exception as _exp:
        print(_exp)


def collect_data(save_path: str):
    t0 = datetime.now()
    driver = get_driver()
    for vacancy in get_sheet():
        driver.switch_to.window(driver.window_handles[0])
        task = Thread(target=get_vacancy_page, args=(driver, vacancy, DATA))
        task.start()
        task.join()
    save_excel(DATA, save_path)
    print(f'Wasted time: {datetime.now() - t0}')
