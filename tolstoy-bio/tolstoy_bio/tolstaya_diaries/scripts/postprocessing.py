import os

import bs4
from tqdm import tqdm

from tolstoy_bio.utilities.io import IoUtils


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ENTRY_XML_DOCUMENT_PATH = os.path.join(ROOT_DIR, "../data/xml/by_entry")
VOLUME_XML_DOCUMENT_PATH = os.path.join(ROOT_DIR, "../data/xml/by_volume")

def main():
    postprocess()

def postprocess():
    remove_initial_cat_ref()
    add_material_cat_ref()
    add_testimony_type_cat_ref()
    add_diaries_materials_cat_ref()
    add_link_to_taxonomy()
    add_author_id()

def get_entry_documents_paths():
    return IoUtils.get_folder_contents_paths(ENTRY_XML_DOCUMENT_PATH)

def get_volume_documents_paths():
    return IoUtils.get_folder_contents_paths(VOLUME_XML_DOCUMENT_PATH)

def get_all_documents_paths():
    return [
        *get_entry_documents_paths(), 
        *get_volume_documents_paths(),
    ]


def remove_initial_cat_ref():
    documents_paths = get_all_documents_paths()

    for path in tqdm(documents_paths):
        content = IoUtils.read_as_text(path)
        soup = bs4.BeautifulSoup(content, "xml")

        cat_ref = soup.find("catRef", attrs={
            "ana": "#diaries",
            "target": "type",
        })

        if cat_ref:
            cat_ref.decompose()

        IoUtils.save_textual_data(soup.prettify(), path)


def add_material_cat_ref():
    documents_paths = get_all_documents_paths()

    for path in tqdm(documents_paths):
        content = IoUtils.read_as_text(path)
        soup = bs4.BeautifulSoup(content, "xml")

        if soup.find("catRef", attrs={
            "ana": "#materials",
            "target": "library",
        }):
            continue

        text_class_element = soup.find("textClass")

        cat_ref_to_add = soup.new_tag("catRef", attrs={
            "ana": "#materials",
            "target": "library",
        })

        text_class_element.append(cat_ref_to_add)
        IoUtils.save_textual_data(soup.prettify(), path)


def add_testimony_type_cat_ref():
    documents_paths = get_all_documents_paths()

    for path in tqdm(documents_paths):
        content = IoUtils.read_as_text(path)
        soup = bs4.BeautifulSoup(content, "xml")

        if soup.find("catRef", attrs={
            "ana": "#testimonies",
            "target": "type",
        }):
            continue

        text_class_element = soup.find("textClass")

        cat_ref_to_add = soup.new_tag("catRef", attrs={
            "ana": "#testimonies",
            "target": "type",
        })

        text_class_element.append(cat_ref_to_add)
        IoUtils.save_textual_data(soup.prettify(), path)


def add_diaries_materials_cat_ref():
    documents_paths = get_all_documents_paths()

    for path in tqdm(documents_paths):
        content = IoUtils.read_as_text(path)
        soup = bs4.BeautifulSoup(content, "xml")

        if soup.find("catRef", attrs={
            "ana": "#diaries_materials",
            "target": "testimonies_type",
        }):
            continue

        text_class_element = soup.find("textClass")

        cat_ref_to_add = soup.new_tag("catRef", attrs={
            "ana": "#diaries_materials",
            "target": "testimonies_type",
        })

        text_class_element.append(cat_ref_to_add)
        IoUtils.save_textual_data(soup.prettify(), path)


def add_link_to_taxonomy():
    documents_paths = get_all_documents_paths()

    for path in tqdm(documents_paths):
        content = IoUtils.read_as_text(path)
        soup = bs4.BeautifulSoup(content, "xml")

        if soup.find("encodingDesc"):
            continue

        file_desc_element = soup.find("fileDesc")

        encoding_desc_element = soup.new_tag("encodingDesc")
        class_decl_element = soup.new_tag("classDecl")
        xi_include_element = soup.new_tag("xi:include", attrs={
            "href": "../../../../../../reference/taxonomy.xml"
        })
        
        encoding_desc_element.append(class_decl_element)
        class_decl_element.append(xi_include_element)
        
        file_desc_element.insert_after(encoding_desc_element)
        IoUtils.save_textual_data(soup.prettify(), path)


def add_author_id():
    documents_paths = get_all_documents_paths()

    for path in tqdm(documents_paths):
        content = IoUtils.read_as_text(path)
        soup = bs4.BeautifulSoup(content, "xml")
        author = soup.find("author")
        
        author.attrs = {
            "ref": "13844",
            "type": "person",
        }

        IoUtils.save_textual_data(soup.prettify(), path)


if __name__ == '__main__':
    main()