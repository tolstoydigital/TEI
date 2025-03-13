import os
import re

import bs4
from tqdm import tqdm

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils
from tolstoy_bio.utilities.io import IoUtils


BIBLLIST_BIO_PATH = os.path.join(
    os.path.dirname(__file__), "../../../reference/bibllist_bio.xml"
)

TOLSTOY_DIARIES_REPOSITORY_PATH = os.path.join(
    os.path.dirname(__file__), "../../../texts/diaries"
)

TOLSTOY_LETTERS_REPOSITORY_PATH = os.path.join(
    os.path.dirname(__file__), "../../../texts/letters"
)


class RelatedItem:
    def __init__(self, soup: bs4.Tag):
        self._soup = soup

    def get_document_id(self):
        return self._soup.find("ref", {"xml:id": True}).attrs["xml:id"].strip()

    def set_persons(self, persons_ids: list[str]) -> None:
        author_id = self._get_author_id()
        other_persons_ids = [id_ for id_ in persons_ids if id_ != author_id]

        existing_relations = self._soup.find_all("relation", {"type": "person"})
        assert existing_relations, "No placeholder found"

        if not other_persons_ids:
            placeholder = self._create_person_relation_placeholder()
            self._replace_relations(existing_relations, [placeholder])
            return

        new_relations: list[bs4.Tag] = []

        for person_id in other_persons_ids:
            new_relation = self._create_person_relation(person_id)
            new_relations.append(new_relation)

        self._replace_relations(existing_relations, new_relations)

    def _replace_relations(
        self, old_relations: list[bs4.Tag], new_relations: list[bs4.Tag]
    ) -> None:
        old_relations[-1].insert_after(*new_relations)
        BeautifulSoupUtils.decompose(*old_relations)

    def _create_person_relation_placeholder(self) -> bs4.Tag:
        return self._create_person_relation("EMPTY")

    def _create_person_relation(self, person_id: str | int) -> bs4.Tag:
        element = bs4.BeautifulSoup("", "xml").new_tag("relation")
        element.attrs = {"ref": person_id, "type": "person"}
        return element

    def _get_author_id(self):
        item = self._soup.parent
        assert item.name == "item", "Unexpected parent"
        return item.find("author").find("person").attrs["id"]


class Item:
    def __init__(self, soup: bs4.Tag):
        self._soup = soup

    def get_related_items(self) -> list[RelatedItem]:
        return [RelatedItem(element) for element in self._soup.find_all("relatedItem")]


class Bibllist:
    @classmethod
    def from_path(cls, path: str):
        soup = BeautifulSoupUtils.create_soup_from_file(path, "xml")

        return cls(soup)

    def __init__(self, soup: bs4.BeautifulSoup):
        self._soup = soup

    def get_item_by_id(self, id_: str) -> Item:
        element = self._soup.find("ref", {"xml:id": id_}).parent
        return Item(element)

    def get_formatted_content(self) -> str:
        return self._soup.prettify()


class Document:
    @classmethod
    def from_path(cls, path: str):
        soup = BeautifulSoupUtils.create_soup_from_file(path, "xml")
        return cls(soup, path)

    def __init__(self, soup: bs4.BeautifulSoup, name: str = "Document"):
        self._soup = soup
        self._name = name

    def get_persons_from_body(self) -> list[str]:
        texts = self._soup.find_all("text")

        assert (
            count := len(texts)
        ) == 1, f"Unexpected number of <text> elements at {self._name}. Expected 1, found {count}."

        text = texts[0]

        names = text.find_all("name", {"ref": True, "type": "person"})

        persons_ids = []

        for name in names:
            person_id: str = name.attrs["ref"]

            if person_id in persons_ids:
                continue

            # TODO: согласовать обработку айдишников с префиксом-дефисом
            if not re.match(r"\d+$", person_id):
                continue

            assert re.match(
                r"\d+$", person_id
            ), f"Unexpected format of a person id: {person_id}"

            persons_ids.append(person_id)

        return persons_ids


def main():
    bibllist = Bibllist.from_path(BIBLLIST_BIO_PATH)

    populate_names_in_bibllist_item(
        bibllist=bibllist,
        item_id="Tolstoy_diaries",
        documents_repository_path=TOLSTOY_DIARIES_REPOSITORY_PATH,
    )

    populate_names_in_bibllist_item(
        bibllist=bibllist,
        item_id="Tolstoy_letters",
        documents_repository_path=TOLSTOY_LETTERS_REPOSITORY_PATH,
    )

    new_content = bibllist.get_formatted_content()
    IoUtils.save_textual_data(new_content, BIBLLIST_BIO_PATH)


def populate_names_in_bibllist_item(
    bibllist: Bibllist, item_id: str, documents_repository_path: str
) -> None:
    item = bibllist.get_item_by_id(item_id)
    related_items = item.get_related_items()

    for related_item in tqdm(related_items, f"Populating names for {item_id}"):
        document_id = related_item.get_document_id()
        document_filename = f"{document_id}.xml"
        document_path = os.path.join(documents_repository_path, document_filename)

        document = Document.from_path(document_path)
        persons_ids = document.get_persons_from_body()
        related_item.set_persons(persons_ids)


if __name__ == "__main__":
    main()
