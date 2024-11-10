from functools import lru_cache, wraps
import os
import re
from typing import Generator

import bs4
from tqdm import tqdm

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils
from tolstoy_bio.utilities.io import IoUtils


BIBLLIST_BIO_PATH = os.path.join(
    os.path.dirname(__file__), "../../../reference/bibllist_bio.xml"
)


TOLSTAYA_DOCUMENTS_REPOSITORY_PATH = os.path.join(
    os.path.dirname(__file__), "../tolstaya_diaries/data/xml/by_entry"
)


class RelatedItem:
    def __init__(self, soup: bs4.Tag):
        self._soup = soup

    def get_document_id(self) -> str:
        return self._soup.find("ref", {"xml:id": True}).attrs["xml:id"].strip()

    def get_opener_text(self) -> str:
        return self._get_opener().text.strip()

    def set_opener_text(self, text: str) -> None:
        opener = self._get_opener()

        assert BeautifulSoupUtils.has_only_navigable_string(opener)

        new_opener_string = bs4.BeautifulSoup("", "xml").new_string(text)
        opener.string.replace_with(new_opener_string)

    def _get_opener(self) -> bs4.Tag:
        return self._soup.find("opener")


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

    def get_tolstaya_diaries_item(self) -> Item:
        return self._get_item_by_id("SAT_diaries")

    def get_tolstaya_journals_item(self) -> Item:
        return self._get_item_by_id("SAT_journals")

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
    def get_last_opener_string(self) -> bs4.NavigableString:
        opener = self._soup.find("opener")
        self._assert(opener, "Failed to find opener")

        string = BeautifulSoupUtils.get_last_navigable_string(opener)
        self._assert(string, "Failed to find the last string of the opener")

        return string

    @_with_loading
    def get_first_string_after_opener(self) -> bs4.NavigableString:
        opener = self._soup.find("opener")
        node_after_opener = opener.next_sibling
        self._assert(node_after_opener, "Failed to find a node after opener")

        string = BeautifulSoupUtils.get_first_navigable_string(node_after_opener)
        self._assert(string, "Failed to find the first string after the opener")

        return string

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


class TolstayaDiariesRepository(DocumentRepository):
    def __init__(self):
        super().__init__(TOLSTAYA_DOCUMENTS_REPOSITORY_PATH)

    def get_documents(self) -> Generator[TeiDocument, None, None]:
        for document in super().get_documents():
            if document.get_id().startswith("tolstaya-s-a-diaries"):
                yield document


class TolstayaJournalsRepository(DocumentRepository):
    def __init__(self):
        super().__init__(TOLSTAYA_DOCUMENTS_REPOSITORY_PATH)

    def get_documents(self) -> Generator[TeiDocument, None, None]:
        for document in super().get_documents():
            if document.get_id().startswith("tolstaya-s-a-journals"):
                yield document


def main():
    print("Loading bibllist_bio.xml data...")

    bibllist = BibllistBio(BIBLLIST_BIO_PATH)

    reconnect_openers_with_body_starts(
        bibllist_bio_item=bibllist.get_tolstaya_diaries_item(),
        document_repository=TolstayaDiariesRepository(),
    )

    reconnect_openers_with_body_starts(
        bibllist_bio_item=bibllist.get_tolstaya_journals_item(),
        document_repository=TolstayaJournalsRepository(),
    )

    print("Saving bibllist_bio.xml...")

    bibllist.save()

    print("Done!")


def reconnect_openers_with_body_starts(
    bibllist_bio_item: Item,
    document_repository: DocumentRepository,
    *,
    verbose: bool = True,
) -> None:
    related_items = bibllist_bio_item.get_related_items()

    related_items_by_id = {
        related_item.get_document_id(): related_item for related_item in related_items
    }

    documents: list[TeiDocument] = document_repository.get_documents()

    documents_by_id: dict[str, TeiDocument] = {
        document.get_id(): document for document in documents
    }

    for document_id, related_item in tqdm(
        related_items_by_id.items(),
        f"Processing {bibllist_bio_item.get_id()}",
        len(related_items_by_id),
        disable=not verbose,
    ):
        document = documents_by_id[document_id]

        document_first_string_after_opener: bs4.NavigableString = (
            document.get_first_string_after_opener()
        )

        if str(document_first_string_after_opener).strip().startswith("."):
            document_last_opener_string: bs4.NavigableString = (
                document.get_last_opener_string()
            )

            document_last_opener_string.replace_with(
                re.sub(r"\.+$", ".", f"{document_last_opener_string}.")
            )

            document_first_string_after_opener.replace_with(
                re.sub(r"^\.+", "", f"{document_first_string_after_opener}".lstrip())
            )

            document.save()

            related_item_opener_text = related_item.get_opener_text()

            related_item.set_opener_text(
                re.sub(r"\.+$", ".", f"{related_item_opener_text}.")
            )


if __name__ == "__main__":
    main()
