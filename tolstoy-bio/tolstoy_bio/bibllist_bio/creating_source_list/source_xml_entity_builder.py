import os
from typing import Self
import bs4
from tqdm import tqdm

from tolstoy_bio.bibllist_bio.creating_source_list.source import Source
from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils


SOURCE_LIST_XML_TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__), "source-list-template.xml"
)


class XmlElement:
    def __init__(self, soup: bs4.Tag):
        self._soup = soup

    def append_element(
        self, name: str, attributes: dict[str, str] = {}, inner_text: str = None
    ) -> Self:
        soup = bs4.BeautifulSoup(features="xml")
        tag = soup.new_tag(name, attrs=attributes)

        if inner_text:
            tag.string = soup.new_string(inner_text)

        self._soup.append(tag)

        return XmlElement(tag)

    def append_element_if_has_inner_text(
        self, name: str, attributes: dict[str, str] = {}, inner_text: str | None = None
    ) -> None:
        if not inner_text:
            return

        return self.append_element(name, attributes, inner_text)

    def append_to(self, element: bs4.Tag) -> None:
        element.append(self._soup)

    def to_soup(self):
        return self._soup


def build_source_xml_entity(source: Source) -> bs4.Tag:
    soup = bs4.BeautifulSoup(f'<item xml:id="{source.id}" n="{source.index}"/>', "xml")

    item_element = XmlElement(soup.find("item"))

    item_element.append_element_if_has_inner_text(
        "title", {"type": "main"}, source.main_title
    )

    item_element.append_element_if_has_inner_text(
        "title", {"type": "bibl"}, source.bibliographic_title
    )

    item_element.append_element_if_has_inner_text("author", inner_text=source.author)

    item_element.append_element_if_has_inner_text("editor", inner_text=source.editor)

    item_element.append_element_if_has_inner_text("title", {"level": "a"}, source.work)

    item_element.append_element_if_has_inner_text(
        "title", {"level": "m"}, source.anthology
    )

    item_element.append_element_if_has_inner_text("biblScope", {}, source.volume)

    item_element.append_element_if_has_inner_text("repository", {}, source.storage)

    if source.publication_place or source.publisher or source.publication_date:
        imprint_element = item_element.append_element("imprint")

        imprint_element.append_element_if_has_inner_text(
            "pubPlace", {}, source.publication_place
        )
        imprint_element.append_element_if_has_inner_text(
            "publisher", {}, source.publisher
        )

        imprint_element.append_element_if_has_inner_text(
            "date", {}, source.publication_date
        )

    return item_element.to_soup()


class XmlSourceListBuilder:
    def __init__(self, sources: list[Source]) -> None:
        self._soup = BeautifulSoupUtils.create_soup_from_file(
            SOURCE_LIST_XML_TEMPLATE_PATH, "xml"
        )

        self._sources = sources

    def build_soup(self) -> bs4.Tag:
        for source in tqdm(self._sources, "Building XML items"):
            item_element = build_source_xml_entity(source)
            self._soup.find("standOff").find("list").append(item_element)

    def save_as_xml(self, path: str):
        BeautifulSoupUtils.prettify_and_save(self._soup, path)
