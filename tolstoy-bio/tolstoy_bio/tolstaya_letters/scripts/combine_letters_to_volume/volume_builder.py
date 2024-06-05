import os
import bs4

from tolstoy_bio.utilities.io import IoUtils

from .entry_content_extractor import get_processed_entry_div


def create_volume(entries_repository_path: str, target_repository_path: str):
    volume_soup = get_initial_volume_template_soup()
    entries_paths = IoUtils.get_folder_contents_paths(entries_repository_path)
    entries_paths.sort()

    for entry_path in entries_paths:
        try:
            entry = get_processed_entry_div(entry_path)
            volume_soup.find("body").append(entry)
        except:
            print(entry_path)
            raise Exception
    
    content = volume_soup.prettify()
    filename = volume_soup.find("title", attrs={"xml:id": True}).attrs["xml:id"]
    filepath = os.path.join(target_repository_path, f"{filename}.xml")

    IoUtils.save_textual_data(content, filepath)


def get_initial_volume_template_soup():
    template_path = get_template_path()
    template_content = IoUtils.read_as_text(template_path)
    return bs4.BeautifulSoup(template_content, "xml")


def get_template_path() -> str:
    module_folder_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(module_folder_path, "template.xml")
