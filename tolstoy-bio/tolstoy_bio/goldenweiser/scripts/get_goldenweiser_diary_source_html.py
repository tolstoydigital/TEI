"""
Автоматическое скачивание дневника Гольденвейзера
в папку ../data/source_html.

1. Сохранение исходных HTML-документов с ФЭБ с добавлением ссылки на источник в разметку.
2. Сохранение автоматически скорректированных версий HTML-документов
(коррекция делается через парсер "html5lib", 
так как оригинальная разметка содержит множество ошибок)
"""


import os

from tolstoy_bio.utilities.feb.provider import FebHtmlProvider


SOURCE_URL = 'https://coollib.com/b/221278-aleksandr-borisovich-goldenveyzer-vblizi-tolstogo-zapiski-za-pyatnadtsat-let/read'

FOLDER_TO_SAVE_SOURCE_HTML = os.path.abspath(os.path.join(__file__, '../../data/source_html/raw'))
FOLDER_TO_SAVE_NORMALIZED_HTML = os.path.abspath(os.path.join(__file__, '../../data/source_html/normalized'))


def main():
    provider = FebHtmlProvider()

    file_name = 'diary.html'
    source_html_saving_path = os.path.join(FOLDER_TO_SAVE_SOURCE_HTML, file_name)
    normalized_html_saving_path = os.path.join(FOLDER_TO_SAVE_NORMALIZED_HTML, file_name)

    document = provider.get(SOURCE_URL)
    document.save_source_html(source_html_saving_path)
    document.save_normalized_html(normalized_html_saving_path, normalizer='html5lib')


if __name__ == '__main__':
    main()