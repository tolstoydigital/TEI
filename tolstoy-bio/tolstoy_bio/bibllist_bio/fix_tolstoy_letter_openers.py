import os
import re

import bs4
from tqdm import tqdm

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils
from tolstoy_bio.utilities.io import IoUtils


BIBLLIST_BIO_PATH = os.path.join(
    os.path.dirname(__file__), "../../../reference/bibllist_bio.xml"
)


leading_asterisk_pattern = re.compile(r"^\*+\s*")
leading_ordinal_number_pattern = re.compile(r"^\d{1,3}[.\s]\s*")


class RelatedItem:
    def __init__(self, soup: bs4.Tag):
        self._soup = soup

    def get_opener_text(self) -> str:
        return self._get_opener().text.strip()

    def set_opener_text(self, text: str) -> None:
        opener = self._get_opener()

        assert (
            len((children := list(opener.children))) == 1
            and children[0] is opener.string
        )

        new_opener_string = bs4.BeautifulSoup("", "xml").new_string(text)
        opener.string.replace_with(new_opener_string)

    def _get_opener(self) -> bs4.Tag:
        return self._soup.find("opener")

    # def fix_opener(self):
    #     opener = self._soup.find("opener")
    #     opener_text = opener.text.strip()
    #     opener_text, n = leading_asterisk_pattern.subn("", opener_text)
    #     opener_text, m = leading_ordinal_number_pattern.subn("", opener_text)

    #     if n > 0 or m > 0:
    #         print(opener_text)

    #     # if re.match(r"\W", opener_text):
    #     # print(opener_text)


class Item:
    def __init__(self, soup: bs4.Tag):
        self._soup = soup

    def get_related_items(self) -> list[RelatedItem]:
        return [RelatedItem(element) for element in self._soup.find_all("relatedItem")]


class Bibllist:
    @classmethod
    def from_path(cls, path: str):
        soup = BeautifulSoupUtils.create_soup_from_file(path, "xml")

        return cls(soup)

    def __init__(self, soup: bs4.BeautifulSoup):
        self._soup = soup

    def get_item_by_id(self, id_: str) -> Item:
        element = self._soup.find("ref", {"xml:id": id_}).parent
        return Item(element)

    def get_formatted_content(self) -> str:
        return self._soup.prettify()


def main():
    bibllist = Bibllist.from_path(BIBLLIST_BIO_PATH)

    item = bibllist.get_item_by_id("Tolstoy_letters")
    related_items = item.get_related_items()

    for related_item in tqdm(related_items, "Processing"):
        opener_text = related_item.get_opener_text()
        opener_text = leading_asterisk_pattern.sub("", opener_text)
        opener_text = leading_ordinal_number_pattern.sub("", opener_text)
        related_item.set_opener_text(opener_text)

    updated_bibllist_content = bibllist.get_formatted_content()
    IoUtils.save_textual_data(updated_bibllist_content, BIBLLIST_BIO_PATH)


if __name__ == "__main__":
    main()
