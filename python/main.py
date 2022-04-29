import os
import asyncio
from typer import Typer, Argument, Option
from head_hunter import async_collect_data
from utils import get_datetime

app = Typer()


@app.command()
def main(mode: str = Argument(None, help='hh.ru, avito'),
         save_path: str = Option(None, help='Path to save'),
         keys_path: str = Option(None, help='Path to search_keys')):
    if mode is None or save_path is None or keys_path is None:
        raise ValueError(f'Run script with arguments MODE --save-path --keys-path')

    save_path = os.path.join(save_path, f'{mode}_{get_datetime()}.xlsx')
    if mode == 'hh.ru':
        asyncio.run(async_collect_data(save_path, keys_path))
    elif mode == 'avito':
        pass


if __name__ == '__main__':
    app()
