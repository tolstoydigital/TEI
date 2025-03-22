"""
Скрипт для импорта CSV-дампа изменённых сущностей-документов bibllist_bio
из БД в локальный файл bibllist_bio.xml

Перед запуском:
- из корня проекта перейти в папку utils ("cd utils");
- проверить, что версия Python не ниже 3.11.5;
- установить зависимости ("pip3 install beautifulsoup4 pandas tqdm").

Стандартная команда для запуска скрипта,
python3 import_csv_database_dump_to_bibllist_bio.py --dump DUMP_PATH
где DUMP_PATH – путь к CSV-файлу-дампу в двойных кавычках.

По умолчанию скрипт обновляет все поля.
Если обновить нужно определённое подмножество полей,
то к команде для запуска скрипта нужно добавить флаг --fields FIELDS,
где FIELDS – список названий полей, которые нужно обновить,
заключённых в двойные кавычки и разделённых пробелом.

Названия полей соответствуют названиям полей класса DocumentMetadata.

Если обновить нужно технические даты,
лучше не забывать указывать и поле под календарные настройки, т. е.
python3 import_csv_database_dump_to_bibllist_bio.py --dump DUMP_PATH --fields "related_works_ids" "calendar_settings"
"""

from argparse import ArgumentParser
from ast import literal_eval
import codecs
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
import os
import re
from typing import Iterator, Self

import bs4
import pandas as pd
from tqdm import tqdm


class RepositoryUtils:
    BIBLLIST_BIO_PATH = os.path.join(
        os.path.dirname(__file__), "../reference/bibllist_bio.xml"
    )


class TextUtils:
    UTC_ENCODING = "utf-8"


class ListUtils:
    @staticmethod
    def get_duplicates(items: list) -> list:
        counts_by_item = defaultdict(int)

        for item in items:
            counts_by_item[item] += 1

        return [value for value, count in counts_by_item.items() if count > 1]


class IoUtils:
    @staticmethod
    def read_as_text(path: str, encoding: str = None) -> str:
        target_encoding = encoding or TextUtils.UTC_ENCODING
        with open(path, "r", encoding=target_encoding) as file:
            return file.read()

    @staticmethod
    def save_textual_data(content: str, path: str, encoding: str = None) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)

        target_encoding = encoding or TextUtils.UTC_ENCODING
        with codecs.open(path, "w", target_encoding) as file:
            file.write(content)


class ValidationUtils:
    @staticmethod
    def validate_value(value, expected_types: list):
        return any(type(value) is expected_type for expected_type in expected_types)

    @classmethod
    def validate_list(cls, values, expected_value_types: list):
        return type(values) is list and all(
            cls.validate_value(value, expected_value_types) for value in values
        )


class BeautifulSoupUtils:
    @staticmethod
    def get_soup_from_file(
        file_path: str, parser: str, encoding: str = TextUtils.UTC_ENCODING
    ) -> bs4.BeautifulSoup:
        file_contents = IoUtils.read_as_text(file_path, encoding)
        return bs4.BeautifulSoup(file_contents, parser)

    @staticmethod
    def get_empty_soup(parser: str = None) -> bs4.BeautifulSoup:
        return bs4.BeautifulSoup(features=parser)

    @classmethod
    def create_tag(cls: Self, parser: str = None, *args, **kwargs) -> bs4.Tag:
        return cls.get_empty_soup(parser).new_tag(*args, **kwargs)

    @classmethod
    def create_string(cls: Self, text: str) -> bs4.Tag:
        return cls.get_empty_soup().new_string(text)

    @staticmethod
    def decompose(*elements: bs4.Tag) -> None:
        for element in elements:
            element.decompose()

    @classmethod
    def replace_sequence_of_tags(
        cls: Self,
        old_sequence: list[bs4.Tag],
        new_sequence: list[bs4.Tag],
        starting_point: bs4.Tag | None = None,
    ) -> None:
        if not old_sequence and not starting_point:
            raise RuntimeError(
                "Unable to replace a sequence of tags "
                "because of an undefined or missing starting point"
            )

        if old_sequence:
            old_sequence[-1].insert_after(*new_sequence)
            BeautifulSoupUtils.decompose(*old_sequence)
        else:
            starting_point.insert_after(*new_sequence)

    @staticmethod
    def has_no_nested_tags(element: bs4.Tag) -> bool:
        return all(type(child) is not bs4.Tag for child in element.children)

    @classmethod
    def set_inner_text(cls, text: str, element: bs4.Tag) -> None:
        element.clear()
        element.append(cls.create_string(text))

    @staticmethod
    def find_if_single_or_fail(soup: bs4.BeautifulSoup, *args, **kwargs) -> bs4.Tag:
        elements = list(soup.find_all(*args, **kwargs))

        if len(elements) != 1:
            raise ValueError(
                f"Expected exactly one element matching {args}, {kwargs}, found {len(elements)}"
            )

        return elements[0]


class DateUtils:
    DATE_STRING_REGEX: str = r"\d{4}-\d{2}-\d{2}"
    DATE_STRING_PATTERN: re.Pattern = re.compile(DATE_STRING_REGEX)
    DATE_STRING_FORMAT: str = r"%Y-%m-%d"

    @classmethod
    def is_date_string(cls: Self, maybe_date_string: str) -> bool:
        return cls.DATE_STRING_PATTERN.fullmatch(maybe_date_string) is not None

    @classmethod
    def assert_date_string(cls: Self, maybe_date_string: str) -> bool:
        assert cls.is_date_string(
            maybe_date_string
        ), f"Unexpected format for the date string: {maybe_date_string}"


@dataclass
class TechnicalDate:
    start_date: str
    end_date: str


class TechnicalDateUtils:
    @staticmethod
    def validate(date: TechnicalDate) -> bool:
        return (
            ValidationUtils.validate_value(date, [TechnicalDate])
            and DateUtils.assert_date_string(date.start_date)
            and DateUtils.assert_date_string(date.end_date)
        )


@dataclass
class CalendarSettings:
    is_in_calendar: bool
    time_span_type: str | None


class CalendarSettingsUtils:
    @staticmethod
    def validate_or_throw(settings: CalendarSettings) -> None:
        if not ValidationUtils.validate_value(settings, [CalendarSettings]):
            raise TypeError(f"The provided value is not a CalendarSettings instance")

        if not ValidationUtils.validate_value(settings.is_in_calendar, [bool]):
            raise TypeError(
                f"Expected a boolean value for is_in_calendar, got {type(settings.is_in_calendar)}"
            )

        if not ValidationUtils.validate_value(settings.time_span_type, [str, None]):
            raise TypeError(
                f"Expected a string or none value for time_span_type, got {type(settings.time_span_type)}"
            )

        if settings.is_in_calendar and settings.time_span_type is None:
            raise ValueError(
                "Expected a defined time_span_type, since is_in_calendar is True."
            )


@dataclass
class DocumentMetadata:
    technical_dates: list[TechnicalDate]
    editor_date_text: str
    opener_text: str
    id: str
    group_id: str
    bibliographic_description: str
    related_persons_ids: list[str | int]
    related_works_ids: list[str | int]
    related_texts_ids: list[str | int]
    related_locations_ids: list[str | int]
    calendar_settings: CalendarSettings


class DocumentMetadataUtils:
    @staticmethod
    def hash_by_id(entries: list[DocumentMetadata]) -> dict[str, DocumentMetadata]:
        return {entry.id: entry for entry in tqdm(entries, "Hashing metadata by ID")}

    @staticmethod
    def assert_no_duplicates(entries: list[DocumentMetadata]) -> None:
        if duplicates := ListUtils.get_duplicates([entry.id for entry in entries]):
            raise AssertionError(
                f"Duplicate entries found in the database dump: {duplicates}"
            )

    @staticmethod
    def validate(entry: DocumentMetadata, fields: set[str] | None = None):
        def validate_technical_dates():
            return ValidationUtils.validate_list(
                entry.technical_dates, [TechnicalDate]
            ) and [TechnicalDateUtils.validate(date) for date in entry.technical_dates]

        def validate_editor_date_text():
            return ValidationUtils.validate_value(entry.editor_date_text, [str])

        def validate_opener_text():
            return ValidationUtils.validate_value(entry.opener_text, [str])

        def validate_id():
            return ValidationUtils.validate_value(entry.id, [str])

        def validate_group_id():
            return ValidationUtils.validate_value(entry.group_id, [str])

        def validate_bibliographic_description():
            return ValidationUtils.validate_value(
                entry.bibliographic_description, [str]
            )

        def validate_related_persons_ids():
            return ValidationUtils.validate_list(entry.related_persons_ids, [str, int])

        def validate_related_works_ids():
            return ValidationUtils.validate_list(entry.related_works_ids, [str, int])

        def validate_related_texts_ids():
            return ValidationUtils.validate_list(entry.related_texts_ids, [str, int])

        def validate_related_locations_ids():
            return ValidationUtils.validate_list(
                entry.related_locations_ids, [str, int]
            )

        def validate_calendar_settings():
            try:
                CalendarSettingsUtils.validate_or_throw(entry.calendar_settings)
                return True
            except TypeError:
                return False

        validators_by_field = {
            "technical_dates": validate_technical_dates,
            "editor_date_text": validate_editor_date_text,
            "opener_text": validate_opener_text,
            "id": validate_id,
            "group_id": validate_group_id,
            "bibliographic_description": validate_bibliographic_description,
            "related_persons_ids": validate_related_persons_ids,
            "related_works_ids": validate_related_works_ids,
            "related_texts_ids": validate_related_texts_ids,
            "related_locations_ids": validate_related_locations_ids,
            "calendar_settings": validate_calendar_settings,
        }

        if fields is None:
            return all(validator() for validator in validators_by_field.values())

        if len(fields) == 0:
            raise ValueError(
                "A list of fields for validation must not be empty if provided."
            )

        return all(validators_by_field[field] for field in fields)


class RelationType(StrEnum):
    PERSON = "person"
    WORK = "works"
    LOCATION = "location"
    SOURCE = "source"
    TEXTS = "texts"


class RelatedItem:
    def __init__(self, soup: bs4.Tag):
        self._soup = soup

    def __str__(self):
        return self._soup.prettify()

    def get_soup(self) -> bs4.BeautifulSoup:
        return self._soup

    def get_id(self) -> str:
        return self._soup.find("ref", {"xml:id": True}).attrs["xml:id"].strip()

    def update(
        self, metadata: DocumentMetadata, fields_to_update: set[str] | None = None
    ) -> None:
        """
        Update the related item's metadata based on the provided DocumentMetadata instance.

        Args:
            metadata: The DocumentMetadata instance containing the new metadata.
            fields_to_update: A list of fields to update. If None, all fields will be updated.
        """
        if fields_to_update is None or "opener_text" in fields_to_update:
            self._set_opener_text(metadata.opener_text)

        if fields_to_update is None or "bibliographic_description" in fields_to_update:
            self._set_bibliographic_description(metadata.bibliographic_description)

        if fields_to_update is None or "editor_date_text" in fields_to_update:
            self._set_editor_date_text(metadata.editor_date_text)

        if fields_to_update is None or "technical_dates" in fields_to_update:
            self._set_technical_dates(metadata.technical_dates)

        if fields_to_update is None or "calendar_settings" in fields_to_update:
            self._set_calendar_settings(metadata.calendar_settings)

        if fields_to_update is None or "related_persons_ids" in fields_to_update:
            self._set_relations(metadata.related_persons_ids, RelationType.PERSON)

        if fields_to_update is None or "related_works_ids" in fields_to_update:
            self._set_relations(metadata.related_works_ids, RelationType.WORK)

        if fields_to_update is None or "related_locations_ids" in fields_to_update:
            self._set_relations(metadata.related_locations_ids, RelationType.LOCATION)

        if fields_to_update is None or "related_texts_ids" in fields_to_update:
            self._set_relations(metadata.related_texts_ids, RelationType.TEXTS)

    def _set_opener_text(self, text: str) -> None:
        opener = self._soup.find("opener")
        self._update_element_text(opener, text)

    def _set_bibliographic_description(self, text: str) -> None:
        bibl_title = self._soup.find("title", {"type": "bibl"})
        self._update_element_text(bibl_title, text)

    def _set_editor_date_text(self, text: str) -> None:
        editor_date = self._soup.find("date", {"type": "editor"})
        self._update_element_text(editor_date, text)

    def _set_calendar_settings(self, settings: CalendarSettings) -> None:
        first_technical_date = self._soup.find("date", {"from": True, "to": True})

        assert (
            first_technical_date
        ), f"Failed to find technical dates at {self.get_id()}, {self._soup.prettify()}"

        first_technical_date.attrs["calendar"] = (
            "FALSE" if settings.is_in_calendar else "TRUE"
        )

        if settings.time_span_type:
            first_technical_date.attrs["period"] = settings.time_span_type
        elif "period" in first_technical_date.attrs:
            del first_technical_date.attrs["period"]

    def _set_relations(
        self, relation_ids: list[str], relation_type: RelationType
    ) -> None:
        existing_relations = self._soup.find_all("relation", {"type": relation_type})

        assert (
            existing_relations
        ), 'No placeholder found for <relation type="{relation_type}" />'

        if not relation_ids:
            placeholder = self._create_placeholder_relation(relation_type)
            BeautifulSoupUtils.replace_sequence_of_tags(
                existing_relations, [placeholder]
            )

            return

        new_relations = [
            self._create_relation(id_, relation_type) for id_ in relation_ids
        ]

        BeautifulSoupUtils.replace_sequence_of_tags(existing_relations, new_relations)

    def _set_technical_dates(self, dates: list[TechnicalDate]) -> None:
        old_date_elements = self._soup.find_all("date", {"from": True, "to": True})

        new_date_elements: list[bs4.Tag] = [
            BeautifulSoupUtils.create_tag(
                "xml",
                "date",
                attrs={
                    "from": date.start_date,
                    "to": date.end_date,
                },
            )
            for date in dates
        ]

        insertion_starting_point = self._soup.find("title", {"type": "bibl"})

        BeautifulSoupUtils.replace_sequence_of_tags(
            old_date_elements, new_date_elements, insertion_starting_point
        )

    def _create_placeholder_relation(self, type_: RelationType) -> bs4.Tag:
        return self._create_relation("EMPTY", type_)

    def _create_relation(self, id_: str | int, type_: RelationType) -> bs4.Tag:
        return BeautifulSoupUtils.create_tag(
            "xml", "relation", attrs={"ref": id_, "type": type_}
        )

    def _update_element_text(self, element: bs4.Tag, text: str) -> None:
        assert BeautifulSoupUtils.has_no_nested_tags(
            element
        ), f"Unsafe element text update: the element <{element.name}> has nested tags."

        if text.strip():
            BeautifulSoupUtils.set_inner_text(text, element)
        else:
            element.clear()


class Item:
    def __init__(self, soup: bs4.Tag) -> None:
        self._soup = soup

    def get_id(self):
        return self._soup.find("ref", {"xml:id": True}).attrs["xml:id"].strip()

    def iterate_related_items(self) -> Iterator[RelatedItem]:
        for element in self._soup.find_all("relatedItem"):
            yield RelatedItem(element)

    def get_related_items_hashed_by_id(self):
        return {
            related_item.get_id(): related_item
            for related_item in self.iterate_related_items()
        }

    def assert_no_related_item_duplicates(self) -> None:
        if duplicates := ListUtils.get_duplicates(
            [related_item.get_id() for related_item in self.iterate_related_items()]
        ):
            raise AssertionError(f"Duplicate related items found: {duplicates}")


class BibllistBio:
    def __init__(self, path: str):
        self._path = path
        self._soup = BeautifulSoupUtils.get_soup_from_file(path, "xml")

    def update_related_items(
        self,
        new_metadata: list[DocumentMetadata],
        fields_to_update: set[str] | None = None,
    ) -> None:
        if len(new_metadata) == 0:
            print("No new data.")
            return

        target_items_ids = set(
            [
                entry.group_id
                for entry in tqdm(new_metadata, "Identifying target <item> element ids")
                if entry.group_id
            ]
        )

        target_items = [
            self._get_item_by_id(item_id)
            for item_id in tqdm(target_items_ids, "Identifying target <item> elements")
        ]

        target_related_items_by_document_id: dict[str, RelatedItem] = {}

        for target_item in tqdm(
            target_items, "Identifying target <relatedItem> elements"
        ):
            target_item.assert_no_related_item_duplicates()
            related_items_by_document_id = target_item.get_related_items_hashed_by_id()

            for document_id, related_item in related_items_by_document_id.items():
                if document_id in target_related_items_by_document_id:
                    print(target_related_items_by_document_id[document_id])
                    raise AssertionError(
                        f"Duplicate document related item found: {document_id}. Item: {target_item.get_id()}"
                    )

                target_related_items_by_document_id[document_id] = related_item

        new_metadata_by_document_id = DocumentMetadataUtils.hash_by_id(new_metadata)

        if any(
            document_id not in target_related_items_by_document_id
            for document_id in new_metadata_by_document_id.keys()
        ):
            missing_ids = [
                document_id
                for document_id in new_metadata_by_document_id.keys()
                if document_id not in target_related_items_by_document_id
            ]

            warning_message = (
                f"Not all related items were found: missing "
                f"{', '.join(missing_ids)}."
            )

            print(warning_message)

            continuation_decision = "placeholder"

            while continuation_decision.lower() not in ["", "y", "n"]:
                continuation_decision = input("Continue anyway? (y/N): ").strip() or "N"

            if continuation_decision != "y":
                raise KeyError(warning_message)

        for document_id, new_metadata in tqdm(
            new_metadata_by_document_id.items(),
            "Updating <relatedItem> elements",
            len(new_metadata_by_document_id),
        ):
            if document_id not in target_related_items_by_document_id:
                continue

            related_item = target_related_items_by_document_id[document_id]
            related_item.update(new_metadata, fields_to_update)

        for related_item in tqdm(
            target_related_items_by_document_id.values(),
            "Post-validating bibllist-bio",
            len(target_related_items_by_document_id),
        ):
            related_item_soup = related_item.get_soup()

            assert BeautifulSoupUtils.find_if_single_or_fail(
                related_item_soup, "ref", {"xml:id": True}
            )

            assert BeautifulSoupUtils.find_if_single_or_fail(
                related_item_soup, "title", {"type": "biodata"}
            )

            assert BeautifulSoupUtils.find_if_single_or_fail(
                related_item_soup, "title", {"type": "bibl"}
            )

            assert related_item_soup.find(
                "date", {"calendar": True, "from": True, "to": True}
            )

            assert BeautifulSoupUtils.find_if_single_or_fail(
                related_item_soup, "date", {"type": "editor"}
            )

            assert related_item_soup.find("catRef", {"ana": True, "target": True})
            
            assert related_item_soup.find("relation", {"ref": True, "type": True})

            assert BeautifulSoupUtils.find_if_single_or_fail(
                related_item_soup, "opener"
            )

    def _get_item_by_id(self, id_: str) -> Item:
        ref_element = self._soup.find("ref", {"xml:id": id_})
        assert ref_element, f"Failed to find <ref> for {id_}"

        item_element = ref_element.parent
        assert item_element.name == "item"

        return Item(item_element)

    def save(self) -> None:
        content = self._soup.prettify()
        IoUtils.save_textual_data(content, self._path)


class DatabaseDumpCsvParser:
    def __init__(self, dump_path: str) -> None:
        self._dump_path = dump_path

    def get_document_metadata_entries(
        self, fields_to_parse: set[str] | None = None
    ) -> list[DocumentMetadata]:
        df = pd.read_csv(self._dump_path, sep=";", dtype=str, keep_default_na=False)

        entries: list[DocumentMetadata] = []

        for _, row in tqdm(df.iterrows(), "Parsing the dump", len(df)):
            entry = DocumentMetadata(
                technical_dates=self._parse_technical_dates(row["dates"]),
                editor_date_text=row["hrdate"],
                opener_text=row["opener"],
                id=row["uid"],
                group_id=row["bibid"],
                bibliographic_description=row["bibtext"],
                related_persons_ids=self._parse_python_literal(row["persons"], []),
                related_works_ids=self._parse_python_literal(row["works"], []),
                related_texts_ids=self._parse_python_literal(row["texts"], []),
                related_locations_ids=self._parse_python_literal(row["places"], []),
                calendar_settings=CalendarSettings(
                    is_in_calendar=self._parse_python_literal(row["incal"]),
                    time_span_type=row["timespan"],
                ),
            )

            DocumentMetadataUtils.validate(entry, fields_to_parse)

            entries.append(entry)

        print("Validating database dump data...")
        DocumentMetadataUtils.assert_no_duplicates(entries)

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
        return re.fullmatch(rf"\[{DateUtils.DATE_STRING_REGEX}", raw_bound) is not None

    def _is_technical_date_ending_including_bound(self, raw_bound: str) -> bool:
        return re.fullmatch(rf"{DateUtils.DATE_STRING_REGEX}\]", raw_bound) is not None

    def _is_technical_date_ending_excluding_bound(self, raw_bound: str) -> bool:
        return re.fullmatch(rf"{DateUtils.DATE_STRING_REGEX}\)", raw_bound) is not None

    def _parse_technical_date_starting_bound(self, raw_bound: str) -> str:
        return self._extract_date_from_string(raw_bound)

    def _parse_technical_date_ending_including_bound(self, raw_bound: str) -> str:
        return self._extract_date_from_string(raw_bound)

    def _parse_technical_date_ending_excluding_bound(self, raw_bound: str) -> str:
        date_string = self._extract_date_from_string(raw_bound)
        date = datetime.strptime(date_string, DateUtils.DATE_STRING_FORMAT)
        lowered_date = date - timedelta(days=1)
        return lowered_date.strftime(DateUtils.DATE_STRING_FORMAT)

    def _extract_date_from_string(self, string: str) -> str:
        return DateUtils.DATE_STRING_PATTERN.search(string).group(0)


def main():
    print("Parsing arguments...")

    cli = ArgumentParser()
    cli.add_argument("--dump", type=str, default=None)
    cli.add_argument("--fields", nargs="*", type=str, default=None)

    arguments = cli.parse_args()

    database_dump_path: str | None = arguments.dump

    if not database_dump_path:
        raise ValueError("Database dump path must be specified as an --dump argument.")

    fields_to_update: set[str] | None = (
        set(arguments.fields) if arguments.fields else None
    )

    print("Arguments parsed.\n")
    print(f"Database dump path: {database_dump_path}")
    print(
        f"Fields to update: {', '.join(fields_to_update) if fields_to_update else 'all'}\n"
    )

    import_dump_to_bibllist_bio(
        database_dump_path, RepositoryUtils.BIBLLIST_BIO_PATH, fields_to_update
    )


def import_dump_to_bibllist_bio(
    dump_path: str, bibllist_bio_path: str, fields_to_update: set[str] | None = None
):
    dump_parser = DatabaseDumpCsvParser(dump_path)
    new_metadata = dump_parser.get_document_metadata_entries(fields_to_update)

    bibllist_bio = BibllistBio(bibllist_bio_path)
    bibllist_bio.update_related_items(new_metadata, fields_to_update)

    print("Saving bibllist_bio.xml...")

    bibllist_bio.save()

    print("Done!")


if __name__ == "__main__":
    main()
