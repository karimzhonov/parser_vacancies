import os
import asyncio
from typer import Typer, Argument, Option
from avito import collect_data as avito_collect_data
from head_hunter import async_collect_data as hh_async_collect_data
from utils import get_datetime

app = Typer()


@app.command()
def main(mode: str = Argument(None, help='hh.ru, avito'),
         save_path: str = Option(None, help='Path to save'),
         keys_path: str = Option(None, help='Path to search_keys')):
    if mode is None or keys_path is None:
        raise ValueError(f'Run script with arguments MODE --save-path --keys-path')

    if save_path is None: save_path = os.path.join('../files', f'{mode}_{get_datetime()}.xlsx')
    if mode == 'hh.ru':
        asyncio.run(hh_async_collect_data(save_path, keys_path))
    elif mode == 'avito':
        avito_collect_data(save_path, keys_path)

if __name__ == '__main__':
    app()
