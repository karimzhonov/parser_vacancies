import re


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
