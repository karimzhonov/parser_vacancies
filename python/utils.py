from datetime import datetime
from fake_useragent import UserAgent


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
