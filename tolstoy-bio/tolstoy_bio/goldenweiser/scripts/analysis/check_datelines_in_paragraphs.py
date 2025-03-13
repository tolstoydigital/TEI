import os

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils
from tolstoy_bio.utilities.dates import DateUtils
from tolstoy_bio.utilities.io import IoUtils


XML_DOCUMENT_PATH = os.path.abspath(os.path.join(__file__, '../../../data/xml/goldenweiser-diaries_1896_1910.xml'))

def main():
    check_datelines_in_paragraphs()


def check_datelines_in_paragraphs():
    xml = BeautifulSoupUtils.create_soup_from_file(XML_DOCUMENT_PATH, "xml")
    elements = xml.find_all()

    entries_started = False

    paragraphs_without_dateline = []
    paragraphs_with_multiple_datelines = []

    for element in elements:
        if not entries_started and element.name == "p" and (year := element.find("year")) and year.text.strip() != "1896":
            entries_started = True

        if entries_started and element.name == "p":
            datelines = element.find_all("dateline")

            if len(datelines) == 0:
                paragraphs_without_dateline.append(element)
            elif len(datelines) > 1:
                paragraphs_with_multiple_datelines.append(element)
            
    content = \
        "paragraphs_without_dateline:\n\n" + \
        "\n\n".join([p.text.strip() for p in paragraphs_without_dateline]) + \
        "\n\n--------\n\nparagraphs_with_multiple_datelines:\n\n" + \
        "\n\n".join([p.text.strip() for p in paragraphs_with_multiple_datelines])


    IoUtils.save_textual_data(
        content=content, 
        path=os.path.abspath(os.path.join(__file__, '../paragraphs_with_unexpected_dateline_count.txt'))
    )


if __name__ == '__main__':
    main()