import time
import pandas as pd
from tqdm import tqdm
from threading import Thread
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from schedule import find_schedule
from excel import get_vacancy_list, save_excel
from utils import get_driver, get_mediana

DATA = {}
URL = f'https://www.avito.ru/rossiya/vakansii'


def find_element(driver, by, value, delay=10) -> WebElement:
    try:
        return WebDriverWait(driver, delay).until(EC.presence_of_element_located((by, value)))
    except TimeoutException:
        print(f'[TimeoutExp] {by} - {value}')
        driver.get(driver.current_url)
        return find_element(driver, by, value, delay)


def find_elements(driver, by, value, delay=10) -> list[WebElement]:
    try:
        return WebDriverWait(driver, delay).until(EC.presence_of_all_elements_located((by, value)))
    except TimeoutException:
        print(f'[TimeoutExp] {driver.current_url} - {by} - {value}')
        driver.get(driver.current_url)
        return find_elements(driver, by, value, delay)


def get_vacancy_data(driver, mediana):
    return_card = {
        'Название': "Не указано",
        'Зарплата(От)': "Не указано",
        'Зарплата(До)': "Не указано",
        'Зарплата(Средняя)': "Не указано",
        'График': "Не указано",
        'Ссылка': "Не указано",
    }
    content = find_element(driver, By.CLASS_NAME, 'item-view-content')
    desc = content.find_element(By.CLASS_NAME, 'item-description').text
    return_card['Название'] = content.find_element(By.CLASS_NAME, 'title-info-title').text
    try:
        price = content.find_element(By.CLASS_NAME, 'price-value-string')
        price = price.find_element(By.CLASS_NAME, 'js-item-price').text.lower()
        if 'от' in price:
            price = price.replace('от', '').replace(' ', '')
            return_card['Зарплата(От)'] = float(price)
            mediana.append(float(price))
        elif 'до' in price:
            price = price.replace('до', '').replace(' ', '')
            return_card['Зарплата(До)'] = float(price)
            mediana.append(float(price))
        elif '—' in price:
            from_p, to_p = price.split('—')
            return_card['Зарплата(От)'] = float(from_p.replace(' ', ''))
            return_card['Зарплата(До)'] = float(to_p.replace(' ', ''))
            return_card['Зарплата(Средняя)'] = (return_card['Зарплата(От)'] + return_card['Зарплата(До)']) / 2
            mediana.append(return_card['Зарплата(Средняя)'])
    except NoSuchElementException:
        pass
    return_card['График'] = find_schedule(desc)
    return_card['Ссылка'] = driver.current_url
    return return_card


def collect_vacancy(driver, items, text, mediana):
    vac_data = []
    for item in tqdm(items, desc=f'Parsing vacancy {text}'):
        item.click()
        driver.switch_to.window(driver.window_handles[1])
        vac_data.append(get_vacancy_data(driver, mediana))
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
    return vac_data


def get_vacancy_page(vacancy, data):
    mediana = []
    text = vacancy['Ключи'].strip('.')
    count = vacancy['Количество вакансии']
    location = vacancy['Локоция']
    driver = get_driver()
    url = f'{URL}?q={text}'
    driver.get(url)
    location_input = find_element(driver, By.XPATH, '//div[@data-marker="search-form/region"]')
    location_input.click()
    location_window = find_element(driver, By.XPATH, '//div[@data-marker="popup-location/overlay"]')
    location_window_input = location_window.find_element(By.XPATH,
                                                         '//input[@data-marker="popup-location/region/input"]')
    location_window_input.send_keys(location)
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
    df = df.sort_values(['График'])
    data[vacancy_name] = df
    print(f'Parsed vacancy: {vacancy_name}')


def collect_data(save_path: str, keys_path: str, async_tasks_count: int = 3):
    t0 = datetime.now()
    counter = 0
    tasks = []
    for vacancy in get_vacancy_list(keys_path).iloc:
        counter += 1
        tasks.append(Thread(target=get_vacancy_page, args=(vacancy, DATA)))
        if counter >= async_tasks_count:
            for task in tasks: task.start()
            counter = 0
            tasks = []
    if len(tasks) > 0:
        for task in tasks: task.start()
        for task in tasks: task.join()
    save_excel(DATA, save_path)
    print(f'Wasted time: {datetime.now() - t0}')
