import os
import re

import bs4
from tqdm import tqdm

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils
from tolstoy_bio.utilities.io import IoUtils
from tolstoy_bio.utilities.tolsoy_digital import TolstoyDigitalUtils


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
VOLUME_XML_DOCUMENT_PATH = os.path.join(ROOT_DIR, "../data/xml/goldenweiser-diaries_1896_1910.xml")
ENTRY_XML_DOCUMENTS_PATH = os.path.join(ROOT_DIR, "../data/xml/by_entry")


def main():
    # wrap_unparagraphed_heads_to_p()
    # add_ids()
    # add_iso_to_dateline_dates()
    # wrap_datelines_into_openers()
    add_biodata_title()
    add_catref_literature_biotopic()
    convert_creation_date_to_calendar_format()
    add_editor_date()


def get_volume_document_path():
    return VOLUME_XML_DOCUMENT_PATH


def get_entry_documents_paths():
    return IoUtils.get_folder_contents_paths(ENTRY_XML_DOCUMENTS_PATH)


def get_all_documents_paths():
    return [
        get_volume_document_path(), 
        *get_entry_documents_paths(),
    ]


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


def add_biodata_title():
    documents_paths = get_all_documents_paths()

    for path in tqdm(documents_paths):
        content = IoUtils.read_as_text(path)
        soup = bs4.BeautifulSoup(content, "xml")

        if soup.find("title", attrs={
            "type": "biodata",
        }):
            continue

        title_stmt = soup.find("titleStmt")
        assert title_stmt, f"<titleStmt> not found in {path}"

        biodata_title = soup.new_tag("title", attrs={
            "type": "biodata",
        })

        biodata_title.append(soup.new_string("Записки А. Б. Гольденвейзера"))

        title_stmt.append(biodata_title)

        IoUtils.save_textual_data(soup.prettify(), path)


def add_catref_literature_biotopic():
    documents_paths = get_all_documents_paths()

    for path in tqdm(documents_paths):
        content = IoUtils.read_as_text(path)
        soup = bs4.BeautifulSoup(content, "xml")

        if soup.find("catRef", attrs={
            "ana": "#literature",
            "target": "biotopic",
        }):
            continue

        text_class_element = soup.find("textClass")

        cat_ref_to_add = soup.new_tag("catRef", attrs={
            "ana": "#literature",
            "target": "biotopic",
        })

        text_class_element.append(cat_ref_to_add)
        IoUtils.save_textual_data(soup.prettify(), path)



def convert_creation_date_to_calendar_format():
    documents_paths = get_all_documents_paths()

    for path in tqdm(documents_paths):
        content = IoUtils.read_as_text(path)
        soup = bs4.BeautifulSoup(content, "xml")

        if soup.find("date", attrs={
            "calendar": True,
        }):
            continue

        creation_element = soup.find("creation")
        date_element = creation_element.find("date")

        if 'when' in date_element.attrs:
            date_element.attrs = {
                'from': date_element.attrs['when'],
                'to': date_element.attrs['when'],
            }
        elif 'notAfter' in date_element.attrs and 'notBefore' in date_element.attrs:
            date_element.attrs = {
                'from': date_element.attrs['notBefore'],
                'to': date_element.attrs['notAfter'],
            }
        elif "from" in date_element.attrs and "to" in date_element.attrs:
            pass
        else:
            raise AssertionError(f"Unexpected date attributes: {date_element.prettify()}")
        
        start_date = date_element.attrs["from"]
        end_date = date_element.attrs["to"]

        if TolstoyDigitalUtils.check_if_two_dates_have_two_week_gap_or_more(start_date, end_date):
            date_element.attrs["calendar"] = "FALSE"
            date_element.attrs["period"] = TolstoyDigitalUtils.get_period_label_given_two_dates(start_date, end_date)
        else:
            date_element.attrs["calendar"] = "TRUE"

        IoUtils.save_textual_data(soup.prettify(), path)


def add_editor_date():
    documents_paths = get_all_documents_paths()

    for path in tqdm(documents_paths):
        content = IoUtils.read_as_text(path)
        soup = bs4.BeautifulSoup(content, "xml")

        if soup.find("date", attrs={
            "type": "editor",
        }):
            continue

        creation_element = soup.find("creation")
        date_element = creation_element.find("date")
        start_date_iso = date_element.attrs["from"]
        end_date_iso = date_element.attrs["to"]
        
        editor_date = soup.new_tag("date", attrs={
            "type": "editor",
        })

        editor_date_label = TolstoyDigitalUtils.format_date_range(start_date_iso, end_date_iso)
        editor_date.append(soup.new_string(editor_date_label))
        creation_element.append(editor_date)

        IoUtils.save_textual_data(soup.prettify(), path)


if __name__ == '__main__':
    main()