from dataclasses import dataclass
import os
from typing import Self
import bs4

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils

from .gusev_bibl_element import GusevBiblElement


@dataclass
class Date:
    year: str
    month: str | None
    day: str | None


@dataclass
class GusevDocumentMetadata:
    start_date: Date
    end_date: Date

    @classmethod
    def from_path(cls, path: str) -> Self:
        filename = os.path.basename(path)
        (
            _,
            _,
            _,
            _,
            start_year,
            start_month,
            start_day,
            end_year,
            end_month,
            end_day,
            *_,
        ) = filename.split("_")

        return cls(
            start_date=Date(start_year, start_month, start_day),
            end_date=Date(end_year, end_month, end_day),
        )


class GusevTeiDocument:
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

    def get_metadata(self) -> GusevDocumentMetadata:
        return GusevDocumentMetadata.from_path(self._path)

    def get_bibl_elements(self) -> list[GusevBiblElement]:
        return [GusevBiblElement(bibl_tag) for bibl_tag in self.get_bibl_tags()]

    def get_bibl_tags(self) -> list[bs4.Tag]:
        return self._get_soup().find_all("bibl")

    def get_technical_dates_as_iso_set(self) -> set[str]:
        iso_set = set()

        technical_dates = self._get_soup().find_all("date", {"from": True, "to": True})
        
        for date in technical_dates:
            iso_set.add(date.attrs["from"])
            iso_set.add(date.attrs["to"])
        
        return iso_set
