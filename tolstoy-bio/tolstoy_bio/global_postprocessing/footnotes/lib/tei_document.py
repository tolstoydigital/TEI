import bs4

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils
from tolstoy_bio.utilities.io import IoUtils
from tolstoy_bio.utilities.xml import XmlUtils

from .tei_note import TeiNote


class TeiDocument:
    _path: str
    _soup: bs4.BeautifulSoup

    def __init__(self, path: str):
        self._path = path
        self._soup = BeautifulSoupUtils.create_soup_from_file(self._path, "xml")

    def get_path(self) -> str:
        return self._path

    def get_id(self) -> str:
        filename = os.path.basename(self._path)
        return filename.replace(".xml", "")

    def get_notes(self) -> list[TeiNote]:
        footnotes: list[TeiNote] = []

        refs = self._soup.find_all("ref")

        for ref in refs:
            next_sibling = BeautifulSoupUtils.get_next_tag_sibling(ref)

            if next_sibling and next_sibling.name == "note":
                footnotes.append(TeiNote(ref, next_sibling))

        return footnotes

    def validate(self) -> None:
        return XmlUtils.validate_xml_or_fail(self._soup.prettify(), ignore_xml_ids=True)

    def save(self) -> None:
        IoUtils.save_textual_data(self._soup.prettify(), self._path)
