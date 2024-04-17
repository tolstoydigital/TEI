import os
import re

import bs4
from tolstoy_bio.utilities.io import IoUtils


def main():
    folder_path = os.path.abspath(os.path.join(__file__, '../../makovitski/data/xml/by_year'))
    file_paths = [os.path.join(folder_path, file_name) for file_name in os.listdir(folder_path)]
    markups = [IoUtils.read_as_text(path) for path in file_paths]

    all_tags = set()

    for markup in markups:
        formatted_markup = bs4.BeautifulSoup(markup, 'xml').prettify()
        formatted_markup = re.sub('\d+', 'N', formatted_markup)
        tags = re.findall(r'<[^>/]+/?>', formatted_markup)
        all_tags.update(tags)

    sorted_tags = sorted(all_tags)
    
    for tag in sorted_tags:
        print(tag)


if __name__ == '__main__':
    main()