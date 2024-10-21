import os
import sys

from tqdm import tqdm

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils
from tolstoy_bio.utilities.io import IoUtils


BIBLLIST_BIO_PATH = os.path.join(
    os.path.dirname(__file__), "../../../reference/bibllist_bio.xml"
)


ADRESSANT = "Л. Н. Толстой."


def main():
    arguments = sys.argv[1:]
    bibllist_bio_path = arguments[0] if arguments else BIBLLIST_BIO_PATH

    soup = BeautifulSoupUtils.create_soup_from_file(bibllist_bio_path, "xml")
    item = soup.find("ref", {"xml:id": "Tolstoy_letters"}).parent
    related_items = item.find_all("relatedItem")

    for related_item in tqdm(related_items, "Adding adressants"):
        title_main = related_item.find("title", {"type": "main"})
        title_main_text = title_main.text.strip()

        assert (
            ADRESSANT not in title_main_text
        ), "Prefix already exists in a title main string."

        new_title_main_text = f"{ADRESSANT} {title_main_text}"

        assert (
            len(list(title_main.children)) == 1
        ), "Unexpected number of children in a title-main."

        title_main.clear()
        title_main.append(soup.new_string(new_title_main_text))

    IoUtils.save_textual_data(soup.prettify(), bibllist_bio_path)


if __name__ == "__main__":
    main()
