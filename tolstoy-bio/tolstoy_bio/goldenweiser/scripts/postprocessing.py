import os
import re

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils
from tolstoy_bio.utilities.io import IoUtils
from tolstoy_bio.utilities.tolsoy_digital import TolstoyDigitalUtils


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
VOLUME_XML_DOCUMENT_PATH = os.path.join(ROOT_DIR, "../data/xml/goldenweiser-diaries_1896_1910.xml")


def main():
    # wrap_unparagraphed_heads_to_p()
    # add_ids()
    add_iso_to_dateline_dates()
    wrap_datelines_into_openers()


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


def add_iso_to_dateline_dates():
    """
    Fixes one wrong date as well.
    """
    
    MONTH_LABEL_TO_NUMBER = {
        'января': '01',
        'февраля': '02',
        'марта': '03',
        'апреля': '04',
        'мая': '05',
        'июня': '06',
        'июля': '07',
        'августа': '08',
        'сентября': '09',
        'октября': '10',
        'ноября': '11',
        'декабря': '12',
    }

    ROMAN_LABEL_TO_NUMBER = {
        'ii': '02',
    }
    
    soup = BeautifulSoupUtils.create_soup_from_file(VOLUME_XML_DOCUMENT_PATH, "xml")
    datelines = soup.find_all("dateline")

    # Mark up dates without years

    for dateline in datelines:
        date = dateline.find("date")
        label = date.text.strip().lower()

        if match := re.match(r"^\d{4}$", label):
            date.attrs['when'] = label
        elif match := re.match(r"^(\w+) (\w+)( (\d{4}))?", label):
            day_label, month_label, _, year_label = match.groups()
            
            day = day_label.zfill(2) if day_label.isdigit() else ROMAN_LABEL_TO_NUMBER[day_label]
            month = MONTH_LABEL_TO_NUMBER[month_label]
            year = year_label or "YYYY"

            date.attrs['when'] = f"{year}-{month}-{day}"
        else:
            raise AssertionError(f"Unexpected date format encountered: {label}")
    
    # Mark up years as well

    current_year = None

    for tag in soup.find_all():
        if tag.name == "year":
            year = tag.text.strip()

            if re.match(r"^\d{4}$", year):
                current_year = year
        
        if tag.name == "dateline":
            date = tag.find("date")

            if "YYYY" in date.attrs.get("when", ""):
                date.attrs["when"] = date.attrs["when"].replace("YYYY", current_year)
    
    # Change erroneous datelines to <susp>

    july_9th_1901_seen = False

    for dateline in soup.find_all("dateline"):
        date = dateline.find("date")
        when = date.attrs.get("when", "")

        if when == "1901-07-09":
            if july_9th_1901_seen:
                dateline.name = "susp"
                break
            else:
                july_9th_1901_seen = True
    
    IoUtils.save_textual_data(soup.prettify(), VOLUME_XML_DOCUMENT_PATH)


def wrap_datelines_into_openers():
    soup = BeautifulSoupUtils.create_soup_from_file(VOLUME_XML_DOCUMENT_PATH, "xml")

    datelines = soup.find_all("dateline")

    for dateline in datelines:
        if BeautifulSoupUtils.has_parent_with_tag_name(dateline, "opener"):
            continue

        if dateline.parent.name == "year":
            dateline.parent.wrap(soup.new_tag("opener"))
        elif dateline.find("date").text.strip() == "17 августа 1922 г.":
            continue
        else:
            dateline.wrap(soup.new_tag("opener"))

    IoUtils.save_textual_data(soup.prettify(), VOLUME_XML_DOCUMENT_PATH)


if __name__ == '__main__':
    main()