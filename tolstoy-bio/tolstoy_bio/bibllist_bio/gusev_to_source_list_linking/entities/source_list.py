import os

from bs4 import BeautifulSoup

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils
from .source_list_entry import SourceListEntry


class SourceList:
    _path: str
    _soup: BeautifulSoup | None = None

    _DEFAULT_PATH: str = os.path.join(
        os.path.dirname(__file__), "../../../../../reference/sourceList.xml"
    )

    def __init__(self, path: str | None = None) -> None:
        self._path = path if path else self._DEFAULT_PATH

    def _get_soup(self) -> BeautifulSoupUtils:
        if self._soup is None:
            self._soup = BeautifulSoupUtils.create_soup_from_file(self._path, "xml")

        return self._soup

    def get_entries(self) -> list[SourceListEntry]:
        soup = self._get_soup()
        list_tag = soup.find("list")
        entry_tags = list_tag.find_all("item")
        return [SourceListEntry(tag) for tag in entry_tags]

    def get_entry_by_id(self, entry_id: str) -> SourceListEntry:
        soup = self._get_soup()
        list_tag = soup.find("list")
        entry_tag = list_tag.find("item", {"xml:id": entry_id})
        return SourceListEntry(entry_tag)
