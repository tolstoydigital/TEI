from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
import os
from typing import Self

from tqdm import tqdm

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils
from tolstoy_bio.utilities.io import IoUtils


module_folder_path = os.path.abspath(os.path.dirname(__file__))

bibllist_bio_path = os.path.join(
    module_folder_path, "../../../reference/bibllist_bio.xml"
)


@dataclass
class Date:
    year: int
    month: int | None = None
    day: int | None = None

    @classmethod
    def from_tei(cls, date_string: str) -> Self:
        components = date_string.split("-")

        match components:
            case [year, month, day]:
                return cls(year, month, day)
            case [year, month]:
                return cls(year, month, None)
            case [year]:
                return cls(year, None, None)
            case _:
                raise ValueError(f"Invalid TEI date format: {date_string}")

    def __init__(self, year: str | int, month: str | int | None, day: str | int | None):
        self.year = int(year)
        self.month = int(month) if month else None
        self.day = int(day) if day else None

    def is_incomplete(self) -> bool:
        return not self.month or not self.day

    def to_datetime(self) -> datetime:
        if self.is_incomplete():
            raise ValueError(
                "Cannot convert Date to Datetime because month or day is not specified."
            )

        return datetime(self.year, self.month, self.day)


class DatePeriod(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


@dataclass
class DateRange:
    start_date: Date
    end_date: Date

    def get_dates_delta(self) -> timedelta:
        datetime_1 = self.end_date.to_datetime()
        datetime_2 = self.start_date.to_datetime()
        return abs(datetime_2 - datetime_1)

    def get_period(self) -> DatePeriod:
        if self.start_date.is_incomplete() or self.end_date.is_incomplete():
            if (
                self.start_date.month
                and self.end_date.month
                and self.start_date.month == self.end_date.month
            ):
                return DatePeriod.WEEKLY

            if self.start_date.year == self.end_date.year:
                return DatePeriod.MONTHLY

            return DatePeriod.YEARLY

        dates_delta = self.get_dates_delta()

        if dates_delta <= timedelta(days=5):
            return DatePeriod.DAILY

        if timedelta(days=5) < dates_delta <= timedelta(days=31):
            return DatePeriod.WEEKLY

        if timedelta(days=31) < dates_delta <= timedelta(days=365):
            return DatePeriod.MONTHLY

        if dates_delta > timedelta(days=365):
            return DatePeriod.YEARLY


def traverse_documents():
    for folder_path, _, filenames in os.walk(
        os.path.abspath(os.path.join(__file__, "../../"))
    ):
        if not filenames:
            continue

        for filename in filenames:
            if filename == "template.xml":
                continue

            if "__pycache__" in folder_path:
                continue

            if not filename.endswith(".xml"):
                continue

            yield os.path.join(folder_path, filename)


def update_document_calendar_period_tags(document_path: str) -> None:
    document_soup = BeautifulSoupUtils.create_soup_from_file(document_path, "xml")
    calendar_tags = document_soup.find_all("date", attrs={"calendar": True})

    for calendar_tag in calendar_tags:
        start_date_string = calendar_tag.attrs["from"]
        end_date_string = calendar_tag.attrs["to"]

        if start_date_string == end_date_string == "1905-12-37":
            start_date_string = end_date_string = calendar_tag.attrs["from"] = (
                calendar_tag.attrs["to"]
            ) = "1905-12-31"

        assert (
            start_date_string and end_date_string
        ), f"Failed to parse dates in {document_path}"

        start_date = Date.from_tei(start_date_string)
        end_date = Date.from_tei(end_date_string)
        date_range = DateRange(start_date, end_date)
        date_period = date_range.get_period()

        if date_period == DatePeriod.DAILY:
            calendar_tag.attrs["calendar"] = "TRUE"

            if "period" in calendar_tag.attrs:
                del calendar_tag.attrs["period"]
        else:
            calendar_tag.attrs["calendar"] = "FALSE"
            calendar_tag.attrs["period"] = date_period

    IoUtils.save_textual_data(document_soup.prettify(), document_path)


def main():
    documents_paths = [*list(traverse_documents()), bibllist_bio_path]

    for document_path in tqdm(documents_paths):
        try:
            update_document_calendar_period_tags(document_path)
        except Exception as e:
            print(document_path)
            raise e


if __name__ == "__main__":
    main()
