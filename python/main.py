import os
import asyncio
from typer import Typer, Argument, Option
from head_hunter import async_collect_data
from utils import get_datetime

app = Typer()


@app.command()
def main(mode: str = Argument(None, help='hh, avito'),
         save_path: str = Option(None, help='Path to save'),
         keys_path: str = Option(None, help='Path to search_keys'),
         count: int = Option(None, help='Count of vacancy')):
    if mode is None or save_path is None or keys_path is None or count:
        raise ValueError(f'Run python {__file__} --help')

    save_path = os.path.join(save_path, f'hh.ru_{get_datetime()}.xlsx')
    if mode == 'hh':
        asyncio.run(async_collect_data(save_path, keys_path, count))


if __name__ == '__main__':
    app()
