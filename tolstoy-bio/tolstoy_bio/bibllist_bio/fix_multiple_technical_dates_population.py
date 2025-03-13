import os
import re

import bs4
from tqdm import tqdm

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils
from tolstoy_bio.utilities.io import IoUtils


BIBLLIST_BIO_PATH = os.path.join(
    os.path.dirname(__file__), "../../../reference/bibllist_bio.xml"
)


TESTIMONIES_REPOSITORY_PATH = os.path.join(
    os.path.dirname(__file__), "../../../tolstoy-bio"
)


class RelatedItem:
    def __init__(self, soup: bs4.Tag):
        self._soup = soup

    def get_document_id(self):
        return self._soup.find("ref", {"xml:id": True}).attrs["xml:id"].strip()

    def add_next_technical_dates(self, configurations: dict[str, str]):
        old_dates = list(self._soup.find_all("date", {"calendar": True}))

        assert (
            len(old_dates) == 1
        ), f"Related item for {self.get_document_id()} unexpectedly has {len(old_dates)} technical dates."

        first_date = old_dates[0]

        assert all(
            [
                self.is_date_valid(c["from"]) and self.is_date_valid(c["to"])
                for c in configurations
            ]
        )

        next_dates = [
            bs4.BeautifulSoup("", "xml").new_tag("date", attrs=attributes)
            for attributes in configurations
        ]

        first_date.insert_after(*next_dates)

    def is_date_valid(self, date: str) -> str:
        return re.match(r"\d{4}-\d{2}-\d{2}$", date) is not None


class Item:
    def __init__(self, soup: bs4.Tag):
        self._soup = soup

    def get_id(self):
        return self._soup.find("ref", {"xml:id": True}).attrs["xml:id"].strip()

    def get_related_items(self) -> list[RelatedItem]:
        return [RelatedItem(element) for element in self._soup.find_all("relatedItem")]


class Bibllist:
    @classmethod
    def from_path(cls, path: str):
        soup = BeautifulSoupUtils.create_soup_from_file(path, "xml")

        return cls(soup)

    def __init__(self, soup: bs4.BeautifulSoup):
        self._soup = soup

    def get_items(self) -> list[Item]:
        body = BeautifulSoupUtils.find_if_single_or_fail(self._soup, "body")
        return [Item(element) for element in body.find_all("item")]

    def get_formatted_content(self) -> str:
        return self._soup.prettify()


class Document:
    @classmethod
    def from_path(cls, path: str, name: str = None):
        soup = BeautifulSoupUtils.create_soup_from_file(path, "xml")
        return cls(soup, name if name is not None else path)

    def __init__(self, soup: bs4.BeautifulSoup, name: str = "Document"):
        self._soup = soup
        self._name = name

    def get_technical_dates_attributes(self) -> list[dict[str, str]]:
        header = self._soup.find("teiHeader")
        dates = header.find_all("date", {"calendar": True})
        return [date.attrs for date in dates]


class DocumentProvider:
    def __init__(self, repository_path: str):
        self._repository_path = repository_path

    def get_path_by_id(self, id_: str) -> Document | None:
        target_filename = f"{id_}.xml"

        for path in self._iterate_document_paths():
            if os.path.basename(path) == target_filename:
                return path

        return None

    def _iterate_document_paths(self):
        for root, _, files in os.walk(self._repository_path):
            for filename in files:
                if filename.endswith(".xml"):
                    yield os.path.join(root, filename)


def main():
    bibllist = Bibllist.from_path(BIBLLIST_BIO_PATH)
    testimony_provider = DocumentProvider(TESTIMONIES_REPOSITORY_PATH)

    items = [
        item
        for item in bibllist.get_items()
        if item.get_id() not in ["Tolstoy_diaries", "Tolstoy_letters"]
    ]

    for item in items:
        for related_item in tqdm(item.get_related_items(), item.get_id()):
            document_id = related_item.get_document_id()
            document_path = testimony_provider.get_path_by_id(document_id)

            if document_path is None:
                continue

            document = Document.from_path(document_path)
            date_configurations = document.get_technical_dates_attributes()

            if len(date_configurations) <= 1:
                continue

            related_item.add_next_technical_dates(date_configurations[1:])

    new_content = bibllist.get_formatted_content()
    IoUtils.save_textual_data(new_content, BIBLLIST_BIO_PATH)


if __name__ == "__main__":
    main()
