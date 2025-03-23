from enum import StrEnum
from typing import Generator
import bs4

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils
from tolstoy_bio.utilities.io import IoUtils


class ItemType(StrEnum):
    TOLSTOY_LETTERS = "Tolstoy_letters"
    TOLSTOY_DIARIES = "Tolstoy_diaries"
    TOLSTAYA_LETTERS = "SAT_letters"
    TOLSTAYA_DIARIES = "SAT_diaries"
    TOLSTAYA_JOURNALS = "SAT_journals"
    MAKOVITSKI = "Makovicky_diaries"
    GOLDENWEISER = "Goldenveizer_diaries"
    GUSEV = "Gusev_letopis"


class RelationType(StrEnum):
    PERSON = "person"
    WORK = "works"
    LOCATION = "location"
    SOURCE = "source"
    TEXTS = "texts"


class SourceRelationType(StrEnum):
    FROM_TOLSTOY_BIO = "tolstoy-bio"
    FROM_SOURCE_LIST = "source-list"


class RelatedItem:
    def __init__(self, soup: bs4.Tag):
        self._soup = soup

    def __str__(self):
        return self._soup.prettify()

    def get_soup(self) -> bs4.BeautifulSoup:
        return self._soup

    def get_id(self) -> str:
        return self._soup.find("ref", {"xml:id": True}).attrs["xml:id"].strip()

    def set_tolstoy_bio_sources(self, source_ids: list[str]) -> None:
        self._set_relations(
            source_ids, RelationType.SOURCE, SourceRelationType.FROM_TOLSTOY_BIO
        )

    def _set_relations(
        self,
        relation_ids: list[str],
        relation_type: RelationType,
        source: str | None = None,
    ) -> None:
        existing_relations = self._soup.find_all("relation", {"type": relation_type})

        if (
            relation_type == RelationType.SOURCE
            and source == SourceRelationType.FROM_TOLSTOY_BIO
            and not existing_relations
        ):
            placeholder = self._create_placeholder_relation(relation_type, source)

            text_type_relations = self._soup.find_all(
                "relation", {"type": RelationType.TEXTS}
            )

            text_type_relations[-1].insert_after(placeholder)

            existing_relations = [placeholder]
        else:
            assert (
                existing_relations
            ), f'No placeholder found for <relation type="{relation_type}" />'

        if not relation_ids:
            placeholder = self._create_placeholder_relation(relation_type, source)

            BeautifulSoupUtils.replace_sequence_of_tags(
                existing_relations, [placeholder]
            )

            return

        new_relations = [
            self._create_relation(id_, relation_type, source) for id_ in relation_ids
        ]

        BeautifulSoupUtils.replace_sequence_of_tags(existing_relations, new_relations)

    def _create_placeholder_relation(
        self, type_: RelationType, source: str | None = None
    ) -> bs4.Tag:
        return self._create_relation("EMPTY", type_, source)

    def _create_relation(
        self, id_: str | int, type_: RelationType, source: str | None = None
    ) -> bs4.Tag:
        tag = BeautifulSoupUtils.create_tag(
            "xml",
            "relation",
            attrs={"ref": id_, "type": type_},
        )

        if source:
            tag["source"] = source

        return tag


class Item:
    def __init__(self, soup: bs4.Tag) -> None:
        self._soup = soup

    def get_id(self) -> str:
        return self._soup.find("ref", {"xml:id": True}).attrs["xml:id"].strip()

    def iterate_related_items(self) -> Generator[RelatedItem, None, None]:
        for element in self._soup.find_all("relatedItem"):
            yield RelatedItem(element)

    def get_related_items_hashed_by_id(self) -> dict[str, RelatedItem]:
        return {
            related_item.get_id(): related_item
            for related_item in self.iterate_related_items()
        }


class BibllistBio:
    def __init__(self, path: str):
        self._path = path
        self._soup = BeautifulSoupUtils.create_soup_from_file(path, "xml")

    def get_gusev_item(self) -> Item:
        return self.get_item_by_type(ItemType.GUSEV)

    def get_item_by_type(self, item_type: ItemType) -> Item:
        return self._get_item_by_id(item_type)

    def _get_item_by_id(self, item_id: str) -> Item:
        element = self._soup.find("ref", {"xml:id": item_id}).parent
        assert element.name == "item"
        return Item(element)

    def save(self) -> None:
        content = self._soup.prettify()
        IoUtils.save_textual_data(content, self._path)
