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
        "accept": "application/json",
        "User-Agent": ua.random
    }
