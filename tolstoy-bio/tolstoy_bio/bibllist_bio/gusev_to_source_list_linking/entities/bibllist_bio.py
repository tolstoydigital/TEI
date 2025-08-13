from dataclasses import dataclass
from enum import StrEnum
import os
from typing import Generator

import bs4

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils
from tolstoy_bio.utilities.io import IoUtils


class ItemType(StrEnum):
    GUSEV = "Gusev_letopis"


class RelationType(StrEnum):
    TEXTS = "texts"
    SOURCE = "source"


class SourceRelationType(StrEnum):
    FROM_TOLSTOY_BIO = "tolstoy-bio"
    FROM_SOURCE_LIST = "source-list"


@dataclass
class BibllistBioSourceListRelationConfiguration:
    bibl_segment_id: str
    source_list_item_id: str
    bibl_point_text: str


class RelatedItem:
    def __init__(self, soup: bs4.Tag):
        self._soup = soup

    def __str__(self):
        return self._soup.prettify()

    def get_soup(self) -> bs4.Tag:
        return self._soup

    def get_id(self) -> str:
        return self._soup.find("ref", {"xml:id": True}).attrs["xml:id"].strip()

    def ensure_placeholders(self):
        self._ensure_tolstoy_bio_source_relation_placeholder_tag()
        self._ensure_source_list_source_relation_placeholder_tag()

    def set_source_list_relations(
        self, sources: list[BibllistBioSourceListRelationConfiguration]
    ):
        existing_relation_tags = self._soup.find_all(
            "relation",
            {
                "type": RelationType.SOURCE,
                "source": SourceRelationType.FROM_SOURCE_LIST,
            },
        )

        if sources:
            new_relation_tags = [
                self._create_source_list_relation_tag(source) for source in sources
            ]

            BeautifulSoupUtils.replace_sequence_of_tags(
                existing_relation_tags,
                new_relation_tags,
            )
        else:
            BeautifulSoupUtils.replace_sequence_of_tags(
                existing_relation_tags,
                [self._create_source_list_source_relation_placeholder_tag()],
            )

    def _ensure_tolstoy_bio_source_relation_placeholder_tag(self):
        last_source_relation_tag = self._get_last_tolstoy_bio_source_relation_tag()

        if not last_source_relation_tag:
            placeholder_tag = self._create_tolstoy_bio_source_relation_placeholder_tag()
            insertion_point_tag = self._get_last_texts_relation_tag()
            insertion_point_tag.insert_after(placeholder_tag)

    def _ensure_source_list_source_relation_placeholder_tag(self):
        last_source_relation_tag = self._get_last_source_list_source_relation_tag()

        if not last_source_relation_tag:
            placeholder_tag = self._create_source_list_source_relation_placeholder_tag()
            insertion_point_tag = self._get_last_tolstoy_bio_source_relation_tag()
            insertion_point_tag.insert_after(placeholder_tag)

    def _get_last_texts_relation_tag(self):
        existent_relation_tags = self._soup.find_all(
            "relation",
            {
                "type": RelationType.TEXTS,
            },
        )

        return existent_relation_tags[-1] if existent_relation_tags else None

    def _get_last_tolstoy_bio_source_relation_tag(self):
        existent_relation_tags = self._soup.find_all(
            "relation",
            {
                "type": RelationType.SOURCE,
                "source": SourceRelationType.FROM_TOLSTOY_BIO,
            },
        )

        return existent_relation_tags[-1] if existent_relation_tags else None

    def _get_last_source_list_source_relation_tag(self):
        existent_relation_tags = self._soup.find_all(
            "relation",
            {
                "type": RelationType.SOURCE,
                "source": SourceRelationType.FROM_SOURCE_LIST,
            },
        )

        return existent_relation_tags[-1] if existent_relation_tags else None

    def _create_tolstoy_bio_source_relation_placeholder_tag(self):
        return self._create_relation_tag(
            ref="EMPTY",
            relation_type=RelationType.SOURCE,
            source=SourceRelationType.FROM_TOLSTOY_BIO,
        )

    def _create_source_list_source_relation_placeholder_tag(self):
        return self._create_relation_tag(
            ref="EMPTY",
            relation_type=RelationType.SOURCE,
            source=SourceRelationType.FROM_SOURCE_LIST,
        )

    def _create_source_list_relation_tag(
        self, source: BibllistBioSourceListRelationConfiguration
    ):
        relation_tag = self._create_relation_tag(
            ref=source.source_list_item_id,
            relation_type=RelationType.SOURCE,
            source=SourceRelationType.FROM_SOURCE_LIST,
            biblSegmentId=source.bibl_segment_id,
        )

        bibl_point = BeautifulSoupUtils.create_tag("xml", "biblpoint")
        BeautifulSoupUtils.set_inner_text(bibl_point, source.bibl_point_text)
        relation_tag.append(bibl_point)

        return relation_tag

    def _create_relation_tag(
        self, *, ref: str, relation_type: RelationType, **kwargs
    ) -> bs4.Tag:
        return BeautifulSoupUtils.create_tag(
            "xml",
            "relation",
            attrs={
                "ref": ref,
                "type": relation_type,
                **kwargs,
            },
        )


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
    _DEFAULT_PATH: str = os.path.join(
        os.path.dirname(__file__), "../../../../../reference/bibllist_bio.xml"
    )

    def __init__(self, path: str | None = None):
        self._path = path if path else self._DEFAULT_PATH
        self._soup = BeautifulSoupUtils.create_soup_from_file(self._path, "xml")

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
