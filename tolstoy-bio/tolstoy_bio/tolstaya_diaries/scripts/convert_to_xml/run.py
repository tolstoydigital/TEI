import os
import re

import bs4

from tolstoy_bio.tolstaya_diaries.scripts.convert_to_xml.converter import TolstayaDiariesFebHtmlToTeiXmlConverter
from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils
from tolstoy_bio.utilities.io import IoUtils


XML_BY_VOLUME_FOLDER_PATH = os.path.abspath(os.path.join(__file__, f'../../../data/xml/by_volume/'))


def main():
    process_documents()


def process_documents():
    source_documents_repository_local_path = f'../../../data/source_html/normalized'
    source_documents_repository_package_path = os.path.join(__file__, source_documents_repository_local_path)
    source_documents_repository_absolute_path = os.path.abspath(source_documents_repository_package_path)

    document_names = IoUtils.get_folder_contents_names(source_documents_repository_absolute_path, ignore_hidden=True)
    document_paths = IoUtils.get_folder_contents_paths(source_documents_repository_absolute_path, ignore_hidden=True)

    for document_name, document_path in zip(document_names, document_paths):
        print(f'Processing file {document_name}...')

        document = TolstayaDiariesFebHtmlToTeiXmlConverter.from_path(document_path)
        document.convert_to_tei()

        processed_document_filename = re.sub(r"\.html?$", ".xml", document_name)

        saving_path = os.path.join(XML_BY_VOLUME_FOLDER_PATH, processed_document_filename)
        document.save_to_file(saving_path)


if __name__ == '__main__':
    main()