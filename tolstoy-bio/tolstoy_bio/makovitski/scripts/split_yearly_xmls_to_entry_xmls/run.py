import collections
import copy
import os

import bs4
from tqdm import tqdm

from tolstoy_bio.utilities.io import IoUtils

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
YEARLY_XML_DOCUMENT_PATH = os.path.join(ROOT_DIR, "../../data/xml/by_year")
DAILY_XML_DOCUMENT_PATH = os.path.join(ROOT_DIR, "../../data/xml/by_entry")


def main():
    document_paths = IoUtils.get_folder_contents_paths(YEARLY_XML_DOCUMENT_PATH)

    for document_path in tqdm(document_paths):
        split_yearly_document_to_daily_documents(document_path)


def split_yearly_document_to_daily_documents(source_xml_path: str):
    source_content = IoUtils.read_as_text(source_xml_path)
    source_soup = bs4.BeautifulSoup(source_content, 'xml')
    source_template = get_tei_without_body_content(source_soup)
    source_entry_containers = source_soup.find_all('div', {'type': 'entry'})

    seen_date_ids = collections.defaultdict(lambda: 1)

    for entry_container in source_entry_containers:
        entry_document, entry_document_id = convert_entry_container_to_entry_document(entry_container, source_template)
        entry_xml_content = entry_document.prettify()

        if entry_document_id in seen_date_ids:
            print(f'Multiple entries on the same date found for {entry_document_id}')
            n_times_seen = seen_date_ids[entry_document_id]
            entry_xml_file_name = f'{entry_document_id}_entry{n_times_seen}.xml'
        else:
            entry_xml_file_name = f'{entry_document_id}.xml'

        entry_xml_file_path = os.path.join(DAILY_XML_DOCUMENT_PATH, entry_xml_file_name)
        IoUtils.save_textual_data(entry_xml_content, entry_xml_file_path)
        seen_date_ids[entry_document_id] += 1


def get_tei_without_body_content(source_tei: bs4.BeautifulSoup):
    tei = copy.copy(source_tei)
    tei.find('body').clear()
    return tei


def convert_entry_container_to_entry_document(entry_container: bs4.BeautifulSoup, tei_template: bs4.BeautifulSoup) -> tuple[bs4.BeautifulSoup, str]:
    document = copy.copy(tei_template)

    # Update header date
    date_element = entry_container.find('date')
    date_iso = date_element.attrs['when']
    creation_date_element = document.find('creation').find('date')
    creation_date_element.attrs = {
        'when': date_iso,
    }

    # Set the document ID
    document_id = generate_document_id(date_iso)
    document_id_tag = document.new_tag('title', attrs={'xml:id': document_id})
    document.find('title').insert_after(document_id_tag)

    # Add the entry content to the template body
    document.find('body').append(entry_container)
    entry_container.unwrap()

    return document, document_id


def generate_document_id(iso_date: str):
    date_components = iso_date.split('-')
    date_code = '_'.join(date_components)
    return f'makovitski_{date_code}'


if __name__ == '__main__':
    main()