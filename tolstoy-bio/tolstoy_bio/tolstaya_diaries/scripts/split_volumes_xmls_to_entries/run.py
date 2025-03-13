import collections
import copy
import enum
import os

import bs4
from tqdm import tqdm

from tolstoy_bio.domain.document_name import DocumentName
from tolstoy_bio.tolstaya_diaries.scripts.utils import tolstaya_s_a_diaries_name_generator, tolstaya_s_a_journals_name_generator
from tolstoy_bio.tolstaya_diaries.scripts.constants import JOURNAL_NAME
from tolstoy_bio.utilities.dictionary import DictionaryUtils
from tolstoy_bio.utilities.io import IoUtils

VOLUME_XML_DOCUMENT_PATH = os.path.abspath(os.path.join(__file__, '../../../data/xml/by_volume'))
ENTRY_XML_DOCUMENT_PATH = os.path.abspath(os.path.join(__file__, '../../../data/xml/by_entry'))


global_document_id_counter = collections.defaultdict(int)


class DiaryType(enum.Enum):
    DIARY = enum.auto()
    JOURNAL = enum.auto()


name_generators_by_diary_type = {
    DiaryType.DIARY: tolstaya_s_a_diaries_name_generator,
    DiaryType.JOURNAL: tolstaya_s_a_journals_name_generator,
}


def main():
    document_names = IoUtils.get_folder_contents_names(VOLUME_XML_DOCUMENT_PATH)
    document_paths = IoUtils.get_folder_contents_paths(VOLUME_XML_DOCUMENT_PATH)

    for document_name, document_path in tqdm(zip(document_names, document_paths), total=len(document_paths)):
        split_compound_document(document_name, document_path)


def split_compound_document(name: str, source_xml_path: str):
    source_content = IoUtils.read_as_text(source_xml_path)
    source_soup = bs4.BeautifulSoup(source_content, 'xml')
    source_template = get_tei_without_body_content(source_soup)
    source_entry_containers = source_soup.find_all('div', {'type': 'entry'})

    for entry_container in source_entry_containers:
        entry_document, entry_document_name = convert_entry_container_to_entry_document(
            entry_container, 
            source_template,
            DiaryType.JOURNAL if name == JOURNAL_NAME.to_filename("xml") else DiaryType.DIARY
        )

        entry_xml_content = entry_document.prettify()
        entry_xml_file_name = entry_document_name.to_filename("xml")
        entry_xml_file_path = os.path.join(ENTRY_XML_DOCUMENT_PATH, entry_xml_file_name)

        assert not IoUtils.is_existent_path(entry_xml_file_path), f"File at path '{entry_xml_file_path}' already exists"
        IoUtils.save_textual_data(entry_xml_content, entry_xml_file_path)


def get_tei_without_body_content(source_tei: bs4.BeautifulSoup):
    tei = copy.copy(source_tei)
    tei.find('body').clear()
    return tei


def convert_entry_container_to_entry_document(entry_container: bs4.BeautifulSoup, tei_template: bs4.BeautifulSoup, diary_type: DiaryType) -> tuple[bs4.BeautifulSoup, DocumentName]:
    document = copy.copy(tei_template)

    # Update header date
    date_element = entry_container.find('date')
    creation_date_element = document.find('creation').find('date')
    creation_date_element.attrs = date_element.attrs

    start_date_iso = DictionaryUtils.get_value_by_first_existent_key(date_element.attrs, 'when', 'from', 'notBefore')
    end_date_iso = DictionaryUtils.get_value_by_first_existent_key(date_element.attrs, 'to', 'notAfter')

    document_name_generator = name_generators_by_diary_type[diary_type]
    document_name = document_name_generator.generate(start_date_iso, end_date_iso)
    document_id = document_name.to_string()

    global_document_id_counter[document_id] += 1
    document_id_count = global_document_id_counter[document_id]

    if document_id_count > 1:
        document_name.postfix = str(document_id_count)
        document_id = document_name.to_string()
    
    new_document_id_tag = document.new_tag('title', attrs={'xml:id': document_id})
    document.find('title').insert_after(new_document_id_tag)

    # Add the entry content to the template body
    document.find('body').append(entry_container)
    entry_container.unwrap()

    return document, document_name


if __name__ == '__main__':
    main()