from functools import lru_cache, wraps
import os
import re
from typing import Generator

import bs4
from tqdm import tqdm

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils


BIBLLIST_BIO_PATH = os.path.join(
    os.path.dirname(__file__), "../../../reference/bibllist_bio.xml"
)


GUSEV_REPOSITORY_PATH = os.path.join(os.path.dirname(__file__), "../gusev/data/tei")


class RelatedItem:
    def __init__(self, soup: bs4.Tag):
        self._soup = soup

    def get_document_id(self) -> str:
        return self._soup.find("ref", {"xml:id": True}).attrs["xml:id"].strip()

    def get_editor_date_text(self) -> str:
        return self._get_editor_date().text.strip()

    def set_editor_date_text(self, text: str) -> None:
        editor_date = self._get_editor_date()

        assert BeautifulSoupUtils.has_only_navigable_string(editor_date)

        new_editor_date_string = bs4.BeautifulSoup("", "xml").new_string(text)
        editor_date.string.replace_with(new_editor_date_string)

    def _get_editor_date(self) -> bs4.Tag:
        return self._soup.find("date", {"type": "editor"})


class Item:
    def __init__(self, soup: bs4.Tag):
        self._soup = soup

    @lru_cache
    def get_id(self) -> str:
        return self._soup.find("ref", {"xml:id": True}).attrs["xml:id"].strip()

    def get_related_items(self) -> list[RelatedItem]:
        return [RelatedItem(element) for element in self._soup.find_all("relatedItem")]


class BibllistBio:
    def __init__(self, path: str):
        soup = BeautifulSoupUtils.create_soup_from_file(path, "xml")
        self._soup = soup
        self._path = path

    def _get_item_by_id(self, id_: str) -> Item:
        element = self._soup.find("ref", {"xml:id": id_}).parent
        return Item(element)

    def get_gusev_item(self) -> Item:
        return self._get_item_by_id("Gusev_letopis")

    def save(self) -> None:
        BeautifulSoupUtils.prettify_and_save(self._soup, self._path)


class TeiDocument:
    _path: str
    _soup: bs4.BeautifulSoup

    def __init__(self, path: str) -> None:
        self._path = path
        self._soup = None

    def get_path(self) -> str:
        return self._path

    def get_id(self) -> str:
        filename = os.path.basename(self._path)
        return filename.replace(".xml", "")

    def load(self):
        self._soup = BeautifulSoupUtils.create_soup_from_file(self._path, "xml")

    def _with_loading(func):
        @wraps(func)
        def method(self, *args, **kwargs):
            if self._soup is None:
                self.load()

            return func(self, *args, **kwargs)

        return method

    def _assert(self, condition: bool, error_message: str) -> None:
        assert condition, f"{error_message} at {self._path}"

    @_with_loading
    def _get_editor_date(self) -> bs4.Tag:
        return BeautifulSoupUtils.find_if_single_or_fail(
            self._soup, "date", {"type": "editor"}
        )

    @_with_loading
    def set_editor_date_text(self, text: str) -> str:
        editor_date = self._get_editor_date()
        assert BeautifulSoupUtils.has_only_navigable_string(editor_date)

        new_editor_date_string = bs4.BeautifulSoup("", "xml").new_string(text)
        editor_date.string.replace_with(new_editor_date_string)

    def save(self) -> None:
        if self._soup is None:
            return

        BeautifulSoupUtils.prettify_and_save(self._soup, self._path)


class DocumentRepository:
    def __init__(self, repository_path: str):
        self._repository_path = repository_path

    def get_documents(self) -> Generator[TeiDocument, None, None]:
        for folder_path, _, filenames in os.walk(self._repository_path):
            if not filenames:
                continue

            for filename in filenames:
                if filename == "template.xml":
                    continue

                if "__pycache__" in folder_path:
                    continue

                if not filename.endswith(".xml"):
                    continue

                path = os.path.join(folder_path, filename)
                yield TeiDocument(path)


class GusevRepository(DocumentRepository):
    def __init__(self):
        super().__init__(GUSEV_REPOSITORY_PATH)


def main():
    print("Loading bibllist_bio.xml data...")

    bibllist = BibllistBio(BIBLLIST_BIO_PATH)

    item: Item = bibllist.get_gusev_item()
    related_items = item.get_related_items()
    related_items_by_id = {item.get_document_id(): item for item in related_items}

    repository = GusevRepository()
    documents = repository.get_documents()
    documents_by_id = {document.get_id(): document for document in documents}

    for document_id, related_item in tqdm(
        related_items_by_id.items(),
        "Updating Gusev's editor dates",
        len(related_items_by_id),
    ):
        editor_date = related_item.get_editor_date_text()
        updated_editor_date = update_editor_date(editor_date)
        related_item.set_editor_date_text(updated_editor_date)

        document = documents_by_id[document_id]
        document.set_editor_date_text(updated_editor_date)
        document.save()

    print("Saving bibllist_bio.xml...")

    bibllist.save()

    print("Done!")


def update_editor_date(editor_date: str) -> str:
    editor_date = re.sub(r" года", "", editor_date, flags=re.IGNORECASE)
    editor_date = re.sub(r"в один из годов ", "", editor_date, flags=re.IGNORECASE)
    editor_date = re.sub(r" год", "", editor_date, flags=re.IGNORECASE)
    editor_date = re.sub(r" г\.", "", editor_date, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", editor_date.strip())


if __name__ == "__main__":
    main()
