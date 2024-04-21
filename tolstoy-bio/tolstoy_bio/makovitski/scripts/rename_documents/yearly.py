import os

import bs4

from tolstoy_bio.makovitski.scripts.utils import generate_name
from tolstoy_bio.utilities.io import IoUtils


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
YEARLY_XML_DOCUMENT_PATH = os.path.join(ROOT_DIR, "../../data/xml/by_year")


def main():
    rename_yearly_documents()


def rename_yearly_documents():
    documents_paths = IoUtils.get_folder_contents_paths(YEARLY_XML_DOCUMENT_PATH)

    for document_path in documents_paths:
        source_filename = os.path.basename(document_path)
        source_name = source_filename.replace('.xml', '')

        if source_name == '1909-till-june':
            new_name = generate_name("1909-01", "1909-06")
        elif source_name == '1909-from-july':
            new_name = generate_name("1909-07", "1909-12")
        else:
            new_name = generate_name(source_name, source_name)
        
        update_document_id_in_xml(document_path, new_name.to_string())
        new_filename = new_name.to_filename('xml')
        new_filepath = os.path.join(YEARLY_XML_DOCUMENT_PATH, new_filename)
        os.rename(document_path, new_filepath)


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