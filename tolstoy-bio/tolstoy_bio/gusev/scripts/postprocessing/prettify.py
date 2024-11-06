import os

from tqdm import tqdm

from tolstoy_bio.utilities.io import IoUtils
from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils


GUSEV_TEI_REPOSITORY_PATH = os.path.join(os.path.dirname(__file__), "../../data/tei")


def main():
    record_paths = IoUtils.get_folder_contents_paths(
        GUSEV_TEI_REPOSITORY_PATH, ignore_hidden=True
    )

    for record_path in tqdm(record_paths, "Prettifying"):
        record_soup = BeautifulSoupUtils.create_soup_from_file(record_path, "xml")
        record_content = record_soup.prettify()
        IoUtils.save_textual_data(record_content, record_path)


if __name__ == "__main__":
    main()
