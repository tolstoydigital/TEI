"""
Скрипт для автоматического скачивания дневников и ежедневников Толстой с ФЭБ
в папку ../data/source_html.
"""


import dataclasses
import os

from tqdm import tqdm

from tolstoy_bio.domain.document_name import DocumentName
from tolstoy_bio.tolstaya_diaries.scripts.constants import FIRST_VOLUME_DIARY_NAME, JOURNAL_NAME, SECOND_VOLUME_DIARY_NAME
from tolstoy_bio.utilities.feb.provider import FebHtmlProvider


@dataclasses.dataclass
class Source :
    name: DocumentName
    url: str


FOLDER_TO_SAVE_SOURCE_HTML = os.path.abspath(os.path.join(__file__, '../../../data/source_html'))


def main():
    download_source_documents()


def download_source_documents():
    diary_1 = Source(FIRST_VOLUME_DIARY_NAME, "https://feb-web.ru/feb/tolstoy/critics/td1/td1-035-.htm")
    diary_2 = Source(SECOND_VOLUME_DIARY_NAME, "https://feb-web.ru/feb/tolstoy/critics/td2/td2-005-.htm")
    journal = Source(JOURNAL_NAME, "https://feb-web.ru/feb/tolstoy/critics/td2/td2-227-.htm")

    sources = [diary_1, diary_2, journal]

    provider = FebHtmlProvider()

    for source in tqdm(sources):
        document = provider.get(source.url)
        filename = source.name.to_filename("html")

        raw_saving_path = os.path.join(FOLDER_TO_SAVE_SOURCE_HTML, "raw", filename)
        document.save_source_html(raw_saving_path)

        normalized_saving_path = os.path.join(FOLDER_TO_SAVE_SOURCE_HTML, "normalized", filename)
        document.save_normalized_html(normalized_saving_path)


if __name__ == '__main__':
    main()
