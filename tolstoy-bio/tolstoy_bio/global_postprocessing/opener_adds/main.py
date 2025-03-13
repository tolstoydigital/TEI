import os

import bs4
from tqdm import tqdm

from tolstoy_bio.utilities.io import IoUtils
from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

TOLSTAYA_LETTER_VOLUME_XML_DOCUMENT_PATH = os.path.join(
    ROOT_DIR, "../../tolstaya_letters/data/tolstaya-s-a-letters.xml"
)

TOLSTAYA_LETTER_ENTRY_XML_DOCUMENTS_FOLDER_PATH = os.path.join(
    ROOT_DIR, "../../tolstaya_letters/data/xml"
)

TOLSTAYA_DIARY_VOLUME_REPOSITORY_PATH = os.path.join(
    ROOT_DIR, "../../tolstaya_diaries/data/xml/by_volume"
)

TOLSTAYA_DIARY_ENTRY_REPOSITORY_PATH = os.path.join(
    ROOT_DIR, "../../tolstaya_diaries/data/xml/by_entry"
)


class TeiDocument:
    def __init__(self, path: str) -> None:
        self._path = path
        self._soup = BeautifulSoupUtils.create_soup_from_file(path, "xml")

    def update_opener_add_tags(self):
        openers = self._soup.find_all("opener")

        for opener in openers:
            adds: list[bs4.Tag] = opener.find_all("add", {"resp": "volume_editor"})

            for add in adds:
                add.name = "respons"

    def save(self) -> bs4.Tag:
        BeautifulSoupUtils.prettify_and_save(self._soup, self._path)


def process_letters():
    document_paths = [
        TOLSTAYA_LETTER_VOLUME_XML_DOCUMENT_PATH,
        *IoUtils.get_folder_contents_paths(
            TOLSTAYA_LETTER_ENTRY_XML_DOCUMENTS_FOLDER_PATH
        ),
    ]

    for path in tqdm(document_paths, "Processing letters"):
        document = TeiDocument(path)
        document.update_opener_add_tags()
        document.save()


def process_diaries():
    document_paths = [
        *IoUtils.get_folder_contents_paths(TOLSTAYA_DIARY_VOLUME_REPOSITORY_PATH),
        *IoUtils.get_folder_contents_paths(TOLSTAYA_DIARY_ENTRY_REPOSITORY_PATH),
    ]

    for path in tqdm(document_paths, "Processing diaries"):
        document = TeiDocument(path)
        document.update_opener_add_tags()
        document.save()


def main() -> None:
    process_letters()
    process_diaries()


if __name__ == "__main__":
    main()
