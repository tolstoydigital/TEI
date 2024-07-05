from collections import defaultdict
import os
from pprint import pprint
import re

import bs4
from tqdm import tqdm

from tolstoy_bio.utilities.io import IoUtils


ROOT_PATH = os.path.abspath(os.path.join(__file__, '../../'))


def main():
    transformation_counts = defaultdict(int)

    for document_path in yield_documents_paths():
        content = IoUtils.read_as_text(document_path)
        
        content, replacement_count = remove_whitespace_between_period_and_comma(content)
        transformation_counts['remove_whitespace_between_period_and_comma'] += replacement_count

        content, replacement_count = add_whitespace_after_year(content)
        transformation_counts['add_whitespace_after_year'] += replacement_count

        content, replacement_count = add_whitespace_after_abbreviation(content)
        transformation_counts['add_whitespace_after_abbreviation'] += replacement_count

        IoUtils.save_textual_data(content, document_path)
    
    pprint(transformation_counts)


def yield_documents_paths(verbose=True):
    for folder_path, _, filenames in os.walk(ROOT_PATH):
        if not filenames:
            continue

        for filename in tqdm(filenames) if verbose else filenames:
            if filename == 'template.xml':
                continue

            if '__pycache__' in folder_path:
                continue
            
            if not filename.endswith('.xml'):
                continue

            yield os.path.join(folder_path, filename)


def remove_whitespace_between_period_and_comma(content: str) -> tuple[str, int]:
    tags = re.findall(r"<.*?>", content)
    assert all(". ," not in tag for tag in tags), "Target substring was found in tag configuration"

    return re.subn(r"\. ,", ".,", content)


def add_whitespace_after_year(content: str) -> tuple[str, int]:
    soup = bs4.BeautifulSoup(content, "xml")
    glued_year_pattern = re.compile(r"(\d{2,})(г?г\.)")

    total_update_count = 0
    
    for text in soup.find_all(string=True):
        updated_string, update_count = glued_year_pattern.subn(r"\1 \2", text.string)
        text.string.replace_with(updated_string)
        total_update_count += update_count

    return soup.prettify(), total_update_count


def add_whitespace_after_abbreviation(content: str) -> tuple[str, int]:
    soup = bs4.BeautifulSoup(content, "xml")
    glued_abbreviation_pattern = re.compile(r"([тс]\.)(\d{1,3})", flags=re.IGNORECASE)

    total_update_count = 0
    
    for text in soup.find_all(string=True):
        updated_string, update_count = glued_abbreviation_pattern.subn(r"\1 \2", text.string)
        text.string.replace_with(updated_string)
        total_update_count += update_count

    return soup.prettify(), total_update_count


if __name__ == '__main__':
    main()