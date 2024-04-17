"""
Скрипт для автоматического скачивание дневников Маковицкого с 1904 по 1910
в папку ../data/source_html.

1. Сохранение исходных HTML-документов с ФЭБ с добавлением ссылки на источник в разметку.
2. Сохранение автоматически скорректированных версий HTML-документов
(на ФЭБ разметка иногда нарушает спецификацию).
"""

import os
from tqdm import tqdm

from tolstoy_bio.utilities.feb.provider import FebHtmlProvider


FOLDER_TO_SAVE_SOURCE_HTML = os.path.abspath(os.path.join(__file__, '../../data/source_html/raw'))
FOLDER_TO_SAVE_NORMALIZED_HTML = os.path.abspath(os.path.join(__file__, '../../data/source_html/normalized'))


def main():
    documents_to_save = {
        '1904': 'http://feb-web.ru/feb/tolstoy/critics/ma1/ma1-093-.htm',
        '1905': 'http://feb-web.ru/feb/tolstoy/critics/ma1/ma1-121-.htm',
        '1906': 'http://feb-web.ru/feb/tolstoy/critics/ma2/ma2-007-.htm',
        '1907': 'http://feb-web.ru/feb/tolstoy/critics/ma2/ma2-346-.htm',
        '1908': 'http://feb-web.ru/feb/tolstoy/critics/ma3/ma3-007-.htm',
        '1909-till-june': 'http://feb-web.ru/feb/tolstoy/critics/ma3/ma3-292-.htm',
        '1909-from-july': 'http://feb-web.ru/feb/tolstoy/critics/ma4/ma4-007-.htm',
        '1910': 'http://feb-web.ru/feb/tolstoy/critics/ma4/ma4-147-.htm'
    }

    provider = FebHtmlProvider()

    for year_label, url in tqdm(
        documents_to_save.items(), 
        desc='Downloading Makovitski\'s diaries 1904-1910'
    ):
        file_name = f'{year_label}.html'
        source_html_saving_path = os.path.join(FOLDER_TO_SAVE_SOURCE_HTML, file_name)
        normalized_html_saving_path = os.path.join(FOLDER_TO_SAVE_NORMALIZED_HTML, file_name)

        document = provider.get(url)
        document.save_source_html(source_html_saving_path)
        document.save_normalized_html(normalized_html_saving_path)


if __name__ == '__main__':
    main()