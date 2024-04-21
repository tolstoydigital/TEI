import os
import re

import bs4
from tqdm import tqdm

from tolstoy_bio.makovitski.scripts.utils import generate_name
from tolstoy_bio.utilities.io import IoUtils


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ENTRY_XML_DOCUMENT_PATH = os.path.join(ROOT_DIR, "../../data/xml/by_entry")


def main():
    rename_entry_documents()


def rename_entry_documents():
    documents_paths = IoUtils.get_folder_contents_paths(ENTRY_XML_DOCUMENT_PATH)

    initial_number_of_documents = len(documents_paths)

    for document_path in tqdm(documents_paths):
        source_filename = os.path.basename(document_path)
        source_name = source_filename.replace('.xml', '')
        source_date_name = source_name.replace('makovitski_', '')

        if 'entry' in source_date_name:
            match = re.search(r'(\d{4})_(\d{2})_(\d{2})_entry(\d\d?)', source_date_name)
            assert match, f'Unexpected name pattern, got: {source_date_name}'

            year, month, day, index = match.groups()
            target_date = '-'.join([year, month, day])
            new_name = generate_name(target_date, target_date, str(index))
        else:
            target_date = '-'.join(source_date_name.split('_'))
            new_name = generate_name(target_date, target_date)
        
        update_document_id_in_xml(document_path, new_name.to_string())
        new_filename = new_name.to_filename('xml')
        new_filepath = os.path.join(ENTRY_XML_DOCUMENT_PATH, new_filename)
        os.rename(document_path, new_filepath)
    
    documents_paths = IoUtils.get_folder_contents_paths(ENTRY_XML_DOCUMENT_PATH)
    assert len(documents_paths) == initial_number_of_documents, "Some documents got lost or elsewise"




def update_document_id_in_xml(document_path: str, new_id: str):
    content = IoUtils.read_as_text(document_path)
    soup = bs4.BeautifulSoup(content, "xml")
    soup_id_title = soup.find('title', attrs={"xml:id": True})

    if soup_id_title:
        soup_id_title.attrs['xml:id'] = new_id
    else:
        soup_title = soup.find('title')
        soup_title.insert_after(soup.new_tag("title", attrs={
            'xml:id': new_id,
        }))
    
    IoUtils.save_textual_data(soup.prettify(), document_path)


if __name__ == "__main__":
    main()