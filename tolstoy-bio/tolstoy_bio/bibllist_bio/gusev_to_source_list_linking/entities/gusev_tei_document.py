import os

import bs4

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils

from .gusev_bibl_segment import GusevBiblSegment


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

    def get_bibl_segments(self) -> list[GusevBiblSegment]:
        segment_tags = self._get_soup().find_all("biblSegment")
        return [GusevBiblSegment(tag, self) for tag in segment_tags]

    def get_bibl_text_by_id(self, bibl_id: str) -> str:
        bibl_tag = self._get_soup().find("bibl", {"id": bibl_id})
        return bibl_tag.text
