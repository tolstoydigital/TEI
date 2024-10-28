from ast import literal_eval
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
import os
import re
import sys
from typing import Iterator

import bs4
import pandas as pd
from pydantic import BaseModel

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils
from tolstoy_bio.utilities.io import IoUtils


BIBLLIST_BIO_PATH = os.path.join(
    os.path.dirname(__file__), "../../../reference/bibllist_bio.xml"
)


date_regex = r"\d{4}-\d{2}-\d{2}"
date_pattern = re.compile(date_regex)


def is_valid_date_string(date_string: str) -> bool:
    return date_pattern.fullmatch(date_string) is not None


@dataclass
class TechnicalDate:
    start_date: str
    end_date: str


def is_valid_technical_date(date: TechnicalDate) -> bool:
    return is_valid_date_string(date.start_date) and is_valid_date_string(date.end_date)


class DocumentMetadata(BaseModel):
    technical_dates: list[TechnicalDate]
    editor_date_text: str
    opener_text: str
    id: str
    group_id: str
    bibliographic_description: str
    related_persons_ids: list[int]
    related_works_ids: list[int]
    related_sources_ids: list[int]
    related_locations_ids: list[int]
    related_persons_ids: list[int]
    is_in_calendar: bool
    time_span_type: str


class RelationType(StrEnum):
    PERSON = "person"
    WORK = "works"
    LOCATION = "location"
    SOURCE = "source"


class RelatedItem:
    def __init__(self, soup: bs4.Tag):
        self._soup = soup

    def get_id(self) -> str:
        return self._soup.find("ref", {"xml:id": True}).attrs["xml:id"].strip()

    def update(self, metadata: DocumentMetadata) -> None:
        self.set_opener_text(metadata.opener_text)
        self.set_bibliographic_description(metadata.bibliographic_description)
        self.set_editor_date_text(metadata.editor_date_text)
        self.set_technical_dates(metadata.technical_dates)
        # TODO: handle is_in_calendar
        # TODO: handle time_span_type

        self.set_relations(metadata.related_persons_ids, RelationType.PERSON)
        self.set_relations(metadata.related_works_ids, RelationType.WORK)
        self.set_relations(metadata.related_locations_ids, RelationType.LOCATION)
        # TODO: add placeholder if it doesn't exist
        # self.set_relations(metadata.related_sources_ids, RelationType.SOURCE)

    def set_opener_text(self, text: str) -> None:
        opener = self._soup.find("opener")
        self._update_element_text(opener, text)

    def set_bibliographic_description(self, text: str) -> None:
        bibl_title = self._soup.find("title", {"type": "bibl"})
        self._update_element_text(bibl_title, text)

    def set_editor_date_text(self, text: str) -> None:
        editor_date = self._soup.find("date", {"type": "editor"})
        self._update_element_text(editor_date, text)

    def set_relations(self, ids: list[str], type_: RelationType) -> None:
        if type_ == RelationType.PERSON:
            author_id = self._get_author_id()
            ids = [id_ for id_ in ids if id_ != author_id]
        elif type_ in [RelationType.WORK, RelationType.SOURCE]:
            document_id = self.get_id()
            ids = [id_ for id_ in ids if id_ != document_id]

        existing_relations = self._soup.find_all("relation", {"type": type_})
        assert existing_relations, "No placeholder found"

        if not ids:
            placeholder = self._create_placeholder_relation(type_)
            self._replace_relations(existing_relations, [placeholder])
            return

        new_relations = [self._create_relation(id_, type_) for id_ in ids]
        self._replace_relations(existing_relations, new_relations)

    def set_technical_dates(self, dates: list[TechnicalDate]) -> None:
        assert all(
            is_valid_technical_date(date) for date in dates
        ), "One or more technical dates have invalid date string format."

        old_date_elements = self._soup.find_all("date", {"calendar": True})

        new_date_elements: bs4.Tag = []

        for date in dates:
            date_element = bs4.BeautifulSoup("", "xml").new_tag(
                "date",
                attrs={
                    "from": date.start_date,
                    "to": date.end_date,
                },
            )

            new_date_elements.append(date_element)

        if old_date_elements:
            old_date_elements[-1].insert_after(*new_date_elements)
            BeautifulSoupUtils.decompose(*old_date_elements)
        else:
            element_before_dates = self._soup.find("title", {"type": "bibl"})
            assert (
                element_before_dates
            ), 'No <title type="bibl"> element has been found.'
            element_before_dates.insert_after(*new_date_elements)

    def _replace_relations(
        self, old_relations: list[bs4.Tag], new_relations: list[bs4.Tag]
    ) -> None:
        old_relations[-1].insert_after(*new_relations)
        BeautifulSoupUtils.decompose(*old_relations)

    def _create_placeholder_relation(self, type_: RelationType) -> bs4.Tag:
        return self._create_relation("EMPTY", type_)

    def _create_relation(self, id_: str | int, type_: RelationType) -> bs4.Tag:
        element = bs4.BeautifulSoup("", "xml").new_tag("relation")
        element.attrs = {"ref": id_, "type": type_}
        return element

    def _get_author_id(self):
        item = self._soup.parent
        assert item.name == "item", "Unexpected parent"
        return item.find("author").find("person").attrs["id"]

    def _update_element_text(self, element: bs4.Tag, text: str) -> None:
        element.clear()
        element.append(bs4.BeautifulSoup("", "xml").new_string(text))


class Item:
    def __init__(self, soup: bs4.Tag):
        self._soup = soup

    def iterate_related_items(self) -> Iterator[RelatedItem]:
        for element in self._soup.find_all("relatedItem"):
            yield RelatedItem(element)

    def get_related_items(self) -> list[RelatedItem]:
        return list(self.iterate_related_items())


class BibllistBio:
    def __init__(self, path: str):
        self._path = path
        self._soup = BeautifulSoupUtils.create_soup_from_file(path, "xml")

    def update_related_items(self, entries: list[DocumentMetadata]) -> None:
        if len(entries) == 0:
            return

        target_items_ids = set([entry.group_id for entry in entries])
        target_items = [self._get_item_by_id(item_id) for item_id in target_items_ids]

        entries_by_id = {entry.id: entry for entry in entries}
        target_related_items_ids = set(entries_by_id.keys())
        target_related_items_by_id: dict[str, RelatedItem] = {}

        for item in target_items:
            for related_item in item.iterate_related_items():
                related_item_id = related_item.get_id()

                if related_item_id not in target_related_items_ids:
                    continue

                target_related_items_by_id[related_item_id] = related_item

                if len(target_related_items_by_id) == len(target_related_items_ids):
                    break
            else:
                continue

            break
        else:
            raise ValueError(
                f"Not all related items were found: missing "
                f"{target_related_items_ids - set(target_related_items_by_id.keys())}."
            )

        for entry_id in target_related_items_ids:
            related_item = target_related_items_by_id[entry_id]
            new_metadata = entries_by_id[entry_id]
            related_item.update(new_metadata)

    def _get_item_by_id(self, id_: str) -> Item:
        element = self._soup.find("ref", {"xml:id": id_}).parent
        return Item(element)

    def save(self) -> None:
        content = self._soup.prettify()
        IoUtils.save_textual_data(content, self._path)


class DatabaseDumpParser:
    def __init__(self, dump_path: str) -> None:
        self._dump_path = dump_path

    def get_document_metadata_entries(self) -> list[DocumentMetadata]:
        df = pd.read_csv(self._dump_path, sep=";", dtype=str, keep_default_na=False)

        entries: list[DocumentMetadata] = []

        for _, row in df.iterrows():
            entry = DocumentMetadata(
                technical_dates=self._parse_technical_dates(row["dates"]),
                editor_date_text=row["hrdate"],
                opener_text=row["opener"],
                id=row["uid"],
                group_id=row["bibid"],
                bibliographic_description=row["bibtext"],
                related_persons_ids=self._parse_python_literal(row["persons"], []),
                related_works_ids=self._parse_python_literal(row["works"], []),
                related_sources_ids=self._parse_python_literal(row["texts"], []),
                related_locations_ids=self._parse_python_literal(row["places"], []),
                is_in_calendar=self._parse_python_literal(row["incal"]),
                time_span_type=row["timespan"],
            )

            entries.append(entry)

        return entries

    def _parse_python_literal(self, value: str, fallback=None):
        if value == "":
            return fallback

        return literal_eval(value)

    def _parse_technical_dates(self, raw_value: str) -> list[TechnicalDate]:
        stringified_date_ranges: list[str] = self._parse_python_literal(raw_value, [])

        technical_dates: list[TechnicalDate] = []

        for stringified_date_range in stringified_date_ranges:
            start_bound, end_bound = stringified_date_range.split(", ")
            start_date = self._parse_technical_date_bound(start_bound)
            end_date = self._parse_technical_date_bound(end_bound)
            technical_date = TechnicalDate(start_date, end_date)
            technical_dates.append(technical_date)

        return technical_dates

    def _parse_technical_date_bound(self, raw_bound: str):
        if self._is_technical_date_starting_bound(raw_bound):
            return self._parse_technical_date_starting_bound(raw_bound)

        if self._is_technical_date_ending_including_bound(raw_bound):
            return self._parse_technical_date_ending_including_bound(raw_bound)

        if self._is_technical_date_ending_excluding_bound(raw_bound):
            return self._parse_technical_date_ending_excluding_bound(raw_bound)

        raise ValueError(f"Unexpected format of a technical date bound: {raw_bound}")

    def _is_technical_date_starting_bound(self, raw_bound: str) -> bool:
        return re.fullmatch(rf"\[{date_regex}", raw_bound) is not None

    def _is_technical_date_ending_including_bound(self, raw_bound: str) -> bool:
        return re.fullmatch(rf"{date_regex}\]", raw_bound) is not None

    def _is_technical_date_ending_excluding_bound(self, raw_bound: str) -> bool:
        return re.fullmatch(rf"{date_regex}\)", raw_bound) is not None

    def _parse_technical_date_starting_bound(self, raw_bound: str) -> str:
        return self._extract_date_from_string(raw_bound)

    def _parse_technical_date_ending_including_bound(self, raw_bound: str) -> str:
        return self._extract_date_from_string(raw_bound)

    def _parse_technical_date_ending_excluding_bound(self, raw_bound: str) -> str:
        date_string = self._extract_date_from_string(raw_bound)
        date = datetime.strptime(date_string, "%Y-%m-%d")
        lowered_date = date - timedelta(days=1)
        return lowered_date.strftime("%Y-%m-%d")

    def _extract_date_from_string(self, string: str) -> str:
        return date_pattern.search(string).group(0)


def main():
    arguments = sys.argv[1:]

    if not arguments:
        raise ValueError("Database dump path must be specified as an argument.")

    database_dump_path, *_ = arguments

    import_dump_to_bibllist_bio(database_dump_path, BIBLLIST_BIO_PATH)


def import_dump_to_bibllist_bio(dump_path: str, bibllist_bio_path: str):
    dump_parser = DatabaseDumpParser(dump_path)
    entries = dump_parser.get_document_metadata_entries()
    bibllist_bio = BibllistBio(bibllist_bio_path)
    bibllist_bio.update_related_items(entries)
    bibllist_bio.save()


if __name__ == "__main__":
    main()
