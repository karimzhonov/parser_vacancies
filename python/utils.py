import logging
from datetime import datetime
from fake_useragent import UserAgent
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver import Chrome, DesiredCapabilities
from webdriver_manager.chrome import ChromeDriverManager


def get_driver():
    """Return Chrome driver"""
    options = Options()
    # options.add_argument("headless")
    options.add_argument("log-level=3")
    options.add_argument("disable-gpu")
    options.add_argument("disable-infobars")
    options.add_argument("disable-extensions")
    options.add_argument(f"user_agent={UserAgent().random}")
    options.add_argument('disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_experimental_option('prefs', {
        'profile.managed_default_content_settings.images': 2,
        'profile.managed_default_content_settings.mixed_script': 2,
        'profile.managed_default_content_settings.media_stream': 2,
        'profile.managed_default_content_settings.stylesheets': 2
    })
    caps = DesiredCapabilities().CHROME
    caps["pageLoadStrategy"] = "normal"  # complete
    driver = Chrome(service=Service(ChromeDriverManager(log_level=logging.CRITICAL).install()),
                    options=options, service_log_path='NULL', desired_capabilities=caps)
    driver.delete_all_cookies()
    return driver

def get_datetime():
    now = str(datetime.now()).split('.')[0]
    now = '___'.join(now.split())
    now = '-'.join(now.split(':'))
    return now


def get_mediana(med):
    n = len(med)
    index = n // 2
    if n % 2:
        return sorted(med)[index]
    return sum(sorted(med)[index - 1:index + 1]) / 2


def get_headers():
    ua = UserAgent()
    return {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "User-Agent": ua.random
    }

