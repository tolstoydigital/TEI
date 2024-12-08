from dataclasses import dataclass
from datetime import datetime, timedelta
import os
import re
import bs4

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils


def convert_range_to_dates(start_date_str, end_date_str) -> list[str]:
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

    dates_list = []

    current_date = start_date
    while current_date <= end_date:
        dates_list.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)

    return dates_list



@dataclass
class TolstoyLetterMetadata:
    volume: int
    number: str
    pages: list[int]


class TolstoyLetterTeiDocument:
    _path: str
    _soup: bs4.BeautifulSoup | None = None

    def __init__(self, path: str):
        self._path = path

    def _assert(self, condition: bool, error_message: str):
        assert condition, f"{error_message} at {self._path}"

    def _get_soup(self) -> bs4.BeautifulSoup:
        if self._soup is None:
            self._soup = BeautifulSoupUtils.create_soup_from_file(self._path, "xml")

        return self._soup

    def get_path(self) -> str:
        return self._path

    def get_id(self) -> str:
        return os.path.basename(self._path).replace(".xml", "")

    def get_volume_number(self) -> int:
        volume_element = BeautifulSoupUtils.find_if_single_or_fail(
            self._get_soup(), "biblScope", {"unit": "vol"}
        )
        volume_number = volume_element.text.strip()

        self._assert(
            volume_number.isdigit(), f"Unexpected volume number: {volume_number}"
        )

        return int(volume_number)

    def get_pages(self) -> list[int]:
        page_element = BeautifulSoupUtils.find_if_single_or_fail(
            self._get_soup(), "biblScope", {"unit": "page"}
        )

        page_element_text = page_element.text.strip()

        if page_element_text.isdigit():
            return [int(page_element_text)]

        if match := re.fullmatch(r"(\d+)-(\d+)", page_element_text):
            start_page, end_page = [int(value) for value in match.groups()]
            return list(range(start_page, end_page + 1))

        self._assert(False, f"Unexpected page format: {page_element_text}")

    def get_number(self) -> str:
        xeno_data_element = BeautifulSoupUtils.find_if_single_or_fail(
            self._get_soup(), "xenoData"
        )

        number_element = BeautifulSoupUtils.find_if_single_or_fail(
            xeno_data_element, "number", {"type": "in a volume"}
        )

        return number_element.text.strip()
    
    def get_metadata(self) -> TolstoyLetterMetadata:
        return TolstoyLetterMetadata(
            volume=self.get_volume_number(),
            number=self.get_number(),
            pages=self.get_pages(),
        )

    def get_creation_dates(self) -> list[str]:
        date_element = self._get_soup().find("creation").find("date")

        if "when" in date_element.attrs:
            return [date_element.attrs["when"]]

        if all(attribute in date_element.attrs for attribute in ["from", "to"]):
            start_date = date_element.attrs["from"]
            end_date = date_element.attrs["to"]

            assert start_date and end_date

            try:
                return convert_range_to_dates(
                    date_element.attrs["from"], date_element.attrs["to"]
                )
            except Exception:
                return []

        return []
