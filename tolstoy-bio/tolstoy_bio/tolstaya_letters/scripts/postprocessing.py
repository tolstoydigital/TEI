import os

import bs4
from tqdm import tqdm

from tolstoy_bio.utilities.io import IoUtils
from tolstoy_bio.utilities.tolsoy_digital import TolstoyDigitalUtils


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ENTRY_XML_DOCUMENT_PATH = os.path.join(ROOT_DIR, "../data/xml")


def main():
    postprocess()


def postprocess():
    # # remove_initial_cat_ref()
    # # add_material_cat_ref()
    # # add_testimony_type_cat_ref()
    # # add_letters_materials_cat_ref()
    # # add_link_to_taxonomy()
    # # add_author_id()
    # # add_author_id_with_nested_person_tag()
    # add_title_main()
    add_biodata_title()
    add_catref_literature_biotopic()
    convert_creation_date_to_calendar_format()
    add_editor_date()


def get_entry_documents_paths():
    return IoUtils.get_folder_contents_paths(ENTRY_XML_DOCUMENT_PATH)


def remove_initial_cat_ref():
    documents_paths = get_entry_documents_paths()

    for path in tqdm(documents_paths):
        content = IoUtils.read_as_text(path)
        soup = bs4.BeautifulSoup(content, "xml")

        cat_ref = soup.find("catRef", attrs={
            "ana": "#letters",
            "target": "type",
        })

        if cat_ref:
            cat_ref.decompose()

        IoUtils.save_textual_data(soup.prettify(), path)


def add_material_cat_ref():
    documents_paths = get_entry_documents_paths()

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
    documents_paths = get_entry_documents_paths()

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


def add_letters_materials_cat_ref():
    documents_paths = get_entry_documents_paths()

    for path in tqdm(documents_paths):
        content = IoUtils.read_as_text(path)
        soup = bs4.BeautifulSoup(content, "xml")

        if soup.find("catRef", attrs={
            "ana": "#letters_materials",
            "target": "testimonies_type",
        }):
            continue

        text_class_element = soup.find("textClass")

        cat_ref_to_add = soup.new_tag("catRef", attrs={
            "ana": "#letters_materials",
            "target": "testimonies_type",
        })

        text_class_element.append(cat_ref_to_add)
        IoUtils.save_textual_data(soup.prettify(), path)


def add_link_to_taxonomy():
    documents_paths = get_entry_documents_paths()

    for path in tqdm(documents_paths):
        content = IoUtils.read_as_text(path)
        soup = bs4.BeautifulSoup(content, "xml")

        if soup.find("encodingDesc"):
            continue

        file_desc_element = soup.find("fileDesc")

        encoding_desc_element = soup.new_tag("encodingDesc")
        class_decl_element = soup.new_tag("classDecl")
        xi_include_element = soup.new_tag("xi:include", attrs={
            "href": "../../../../../reference/taxonomy.xml"
        })
        
        encoding_desc_element.append(class_decl_element)
        class_decl_element.append(xi_include_element)
        
        file_desc_element.insert_after(encoding_desc_element)
        IoUtils.save_textual_data(soup.prettify(), path)


def add_author_id():
    documents_paths = get_entry_documents_paths()

    for path in tqdm(documents_paths):
        content = IoUtils.read_as_text(path)
        soup = bs4.BeautifulSoup(content, "xml")
        author = soup.find("author")

        if "ref" in author.attrs:
            continue
        
        author.attrs = {
            "ref": "13844",
            "type": "person",
        }

        IoUtils.save_textual_data(soup.prettify(), path)


def add_author_id_with_nested_person_tag():
    documents_paths = get_entry_documents_paths()

    for path in tqdm(documents_paths):
        content = IoUtils.read_as_text(path)
        soup = bs4.BeautifulSoup(content, "xml")
        element = soup.find("author")

        if element.find("person"):
            continue

        element.name = "person"
        
        element.attrs = {
            "ref": "13844"
        }
        
        element.wrap(soup.new_tag("author"))

        IoUtils.save_textual_data(soup.prettify(), path)


def add_title_main():
    documents_paths = get_entry_documents_paths()

    for path in tqdm(documents_paths):
        content = IoUtils.read_as_text(path)
        soup = bs4.BeautifulSoup(content, "xml")

        if soup.find("title", attrs={
            "type": "main"
        }):
            continue

        title_main = soup.new_tag("title", attrs={
            "type": "main"
        })

        title_main.append(soup.new_string("Толстая С.А. Письма к Л.Н. Толстому"))

        title_stmt = soup.find("titleStmt")
        title = title_stmt.find("title")
        title.insert_after(title_main)

        IoUtils.save_textual_data(soup.prettify(), path)


def add_biodata_title():
    documents_paths = get_entry_documents_paths()

    for path in tqdm(documents_paths, desc="add_biodata_title"):
        content = IoUtils.read_as_text(path)
        soup = bs4.BeautifulSoup(content, "xml")
        title_stmt = soup.find("titleStmt")

        assert title_stmt, f"<titleStmt> not found in {path}"

        if soup.find("title", attrs={
            "type": "biodata",
        }):
            continue

        biodata_title = soup.new_tag("title", attrs={
            "type": "biodata",
        })

        biodata_title.append(soup.new_string("Письмо Софьи Андреевны Толстой мужу"))

        title_stmt.append(biodata_title)

        IoUtils.save_textual_data(soup.prettify(), path)


def add_catref_literature_biotopic():
    documents_paths = get_entry_documents_paths()

    for path in tqdm(documents_paths, desc="add_catref_literature_biotopic"):
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
    documents_paths = get_entry_documents_paths()

    for path in tqdm(documents_paths, desc="convert_creation_date_to_calendar_format"):
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
    documents_paths = get_entry_documents_paths()

    for path in tqdm(documents_paths, desc="add_editor_date"):
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