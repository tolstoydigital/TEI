import os

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils
from tolstoy_bio.utilities.io import IoUtils
from tolstoy_bio.utilities.tolsoy_digital import TolstoyDigitalUtils


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
VOLUME_XML_DOCUMENT_PATH = os.path.join(ROOT_DIR, "../data/xml/goldenweiser-diaries_1896_1910.xml")


def main():
    wrap_unparagraphed_heads_to_p()
    add_ids()


def wrap_unparagraphed_heads_to_p():
    soup = BeautifulSoupUtils.create_soup_from_file(VOLUME_XML_DOCUMENT_PATH, "xml")
    heads = soup.find_all("head")

    for head in heads:
        if BeautifulSoupUtils.has_parent_with_tag_name(head, "p"):
            continue

        if head.find("p") is not None:
            raise AssertionError("<head> has <p> as children")
        
        head.wrap(soup.new_tag("p"))
    
    IoUtils.save_textual_data(soup.prettify(), VOLUME_XML_DOCUMENT_PATH)


def add_ids():
    soup = BeautifulSoupUtils.create_soup_from_file(VOLUME_XML_DOCUMENT_PATH, "xml")
    TolstoyDigitalUtils.add_unique_ids_to_paragraphs(soup)
    IoUtils.save_textual_data(soup.prettify(), VOLUME_XML_DOCUMENT_PATH)


if __name__ == '__main__':
    main()