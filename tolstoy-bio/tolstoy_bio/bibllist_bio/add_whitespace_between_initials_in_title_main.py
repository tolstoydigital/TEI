import os
import re

import bs4
from tqdm import tqdm

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils
from tolstoy_bio.utilities.io import IoUtils


BIBLLIST_BIO_PATH = os.path.join(
    os.path.dirname(__file__), "../../../reference/bibllist_bio.xml"
)

glued_initials_pattern = re.compile(r"(([А-ЯЁA-Z]\.){2,})")
letter_after_period_pattern = re.compile(r"\.[А-ЯЁA-Z]")


class Bibllist:
    @classmethod
    def from_path(cls, path: str):
        soup = BeautifulSoupUtils.create_soup_from_file(path, "xml")

        return cls(soup)

    def __init__(self, soup: bs4.BeautifulSoup):
        self.soup = soup

    def get_body_title_main_elements(self) -> bs4.Tag:
        return self.soup.find("body").find_all("title", {"type": "main"})

    def get_formatted_content(self) -> str:
        return self.soup.prettify()


def main():
    bibllist = Bibllist.from_path(BIBLLIST_BIO_PATH)
    title_main_elements = bibllist.get_body_title_main_elements()

    for title_main in tqdm(title_main_elements, "Splitting glued initials"):
        assert BeautifulSoupUtils.has_only_navigable_string(title_main)
        title_main_text = title_main.text.strip()

        def add_spaces(match: re.Match) -> str:
            return re.sub(r"\.", ". ", match.group(0))

        updated_title_main_text = glued_initials_pattern.sub(
            add_spaces, title_main_text
        )
        updated_title_main_text = re.sub(r"\s+", " ", updated_title_main_text)

        title_main.clear()
        title_main.append(bibllist.soup.new_string(updated_title_main_text))

        assert glued_initials_pattern.search(title_main.text) is None

        if letter_after_period_pattern.search(title_main.text):
            updated_title_main_text = re.sub(r"\.", ". ", updated_title_main_text)
            updated_title_main_text = re.sub(r"\s+", " ", updated_title_main_text)

            title_main.clear()
            title_main.append(bibllist.soup.new_string(updated_title_main_text.strip()))

            assert (
                letter_after_period_pattern.search(title_main.text) is None
            ), title_main.text

    updated_bibllist_content = bibllist.get_formatted_content()
    IoUtils.save_textual_data(updated_bibllist_content, BIBLLIST_BIO_PATH)


if __name__ == "__main__":
    main()
