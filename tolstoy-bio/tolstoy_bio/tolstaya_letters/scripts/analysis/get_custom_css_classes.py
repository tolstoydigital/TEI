import os
import re

import bs4
from tqdm import tqdm
from tolstoy_bio.utilities.io import IoUtils


def main():
    get_custom_css_classes()


def get_custom_css_classes():
    source_documents_repository_local_path = f'../../../data/source_html/normalized'
    source_documents_repository_package_path = os.path.join(__file__, source_documents_repository_local_path)
    source_documents_repository_absolute_path = os.path.abspath(source_documents_repository_package_path)
    folder_paths = IoUtils.get_folder_contents_paths(source_documents_repository_absolute_path, ignore_hidden=True)

    all_found_classes = set()

    for folder_path in tqdm(folder_paths):
        files_paths = IoUtils.get_folder_contents_paths(folder_path, ignore_hidden=True)

        for file_path in files_paths:
            file_content = IoUtils.read_as_text(file_path, encoding='utf-8')
            file_tree = bs4.BeautifulSoup(file_content, 'lxml')
            style_element = file_tree.find('style')
            custom_css = style_element.text

            custom_css_classes = get_classes_from_css(custom_css)
            all_found_classes.update(custom_css_classes)

            custom_css_p_classes = get_p_classes_from_css(custom_css)
            all_found_classes.update(custom_css_p_classes)

    print('\n'.join(sorted(all_found_classes)))


def get_classes_from_css(css: str) -> list[str]:
    css_without_styles = re.sub(r'\{.*?\}', ' ', css, flags=re.MULTILINE)
    processed_css_without_styles = re.sub(r'\s+', ' ', css_without_styles)
    css_classes = processed_css_without_styles.split(' ')
    return css_classes


def get_p_classes_from_css(css: str) -> list[str]:
    p_classes = re.findall(r"p\.[\w-]+", css)
    return p_classes


if __name__ == '__main__':
    main()
