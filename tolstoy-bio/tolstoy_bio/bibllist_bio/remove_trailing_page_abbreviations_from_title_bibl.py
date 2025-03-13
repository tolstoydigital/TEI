import os
import re
import sys

import bs4
from tqdm import tqdm

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils
from tolstoy_bio.utilities.io import IoUtils


BIBLLIST_BIO_PATH = os.path.join(
    os.path.dirname(__file__), "../../../reference/bibllist_bio.xml"
)


trailing_page_abbreviation_pattern = re.compile(r"(^|\s)С\.$", flags=re.IGNORECASE)


def main():
    arguments = sys.argv[1:]
    bibllist_bio_path = arguments[0] if arguments else BIBLLIST_BIO_PATH

    soup = BeautifulSoupUtils.create_soup_from_file(bibllist_bio_path, "xml")

    title_bibl_elements: list[bs4.Tag] = soup.find_all("title", {"type": "bibl"})

    update_count = 0

    for title_bibl in tqdm(title_bibl_elements, "Processing"):
        assert (
            len(list(title_bibl.children)) == 1
        ), f"Unexpected number of children in {title_bibl.prettify()}"

        title_bibl_text = title_bibl.text.strip()

        if trailing_page_abbreviation_pattern.search(title_bibl_text):
            updated_title_bibl_text, replacement_count = re.subn(
                r"\s*С\.$", "", title_bibl_text
            )

            assert (
                replacement_count == 1
            ), f"Expected 1 replacement, got {replacement_count}."
            
            assert (
                updated_title_bibl_text in title_bibl_text
            ), f'Expected replacement at the end of the original string "{title_bibl_text}", found within instead: "{updated_title_bibl_text}".'

            title_bibl.clear()
            title_bibl.append(soup.new_string(updated_title_bibl_text))

            update_count += 1

    print(f"Done! Number of replacements: {update_count}")

    IoUtils.save_textual_data(soup.prettify(), bibllist_bio_path)


if __name__ == "__main__":
    main()
