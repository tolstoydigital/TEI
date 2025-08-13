import os
from uuid import uuid4

from bs4 import BeautifulSoup, Tag
from tqdm import tqdm

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils
from tolstoy_bio.utilities.io import IoUtils


def main():
    assign_ids_to_bibl_tags()
    add_segments_to_gusev_documents()


def assign_ids_to_bibl_tags():
    for path in tqdm(
        _get_gusev_documents_paths(), "Assigning unique IDs to Gusev <bibl> tags"
    ):
        soup: BeautifulSoup = BeautifulSoupUtils.create_soup_from_file(path, "xml")
        bibl_tags = soup.find_all("bibl")

        if not bibl_tags:
            continue

        for tag in bibl_tags:
            tag.attrs["id"] = uuid4()

        BeautifulSoupUtils.prettify_and_save(soup, path)


def _get_gusev_documents_paths():
    module_folder_relative_path = os.path.dirname(__file__)
    module_folder_absolute_path = os.path.abspath(module_folder_relative_path)
    documents_repository_path = os.path.join(module_folder_absolute_path, "../data/tei")
    return IoUtils.get_folder_contents_paths(documents_repository_path)


def add_segments_to_gusev_documents():
    for path in tqdm(
        _get_gusev_documents_paths(), "Adding segments to Gusev documents"
    ):
        soup: BeautifulSoup = BeautifulSoupUtils.create_soup_from_file(path, "xml")

        bibl_list_tags = soup.find_all("listBibl")

        if len(bibl_list_tags) > 1:
            raise AssertionError(f"Multiple <listBibl> tags encountered at {path}")

        if len(bibl_list_tags) == 0:
            continue

        bibl_list_tag: Tag = bibl_list_tags[0]

        new_segment_list_tag = soup.new_tag("listBiblSegment")
        bibl_list_tag.insert_after(new_segment_list_tag)

        bibl_tags = bibl_list_tag.find_all("bibl")

        for bibl_tag in bibl_tags:
            bibl = bibl_tag.text.strip()
            segments = [segment.strip() for segment in bibl.split(";")]

            for segment in segments:
                new_segment_tag = soup.new_tag("biblSegment")

                new_segment_tag.attrs = {
                    "id": uuid4(),
                    "parentBiblId": bibl_tag.attrs["id"],
                }

                BeautifulSoupUtils.set_inner_text(new_segment_tag, segment)

                new_segment_list_tag.append(new_segment_tag)

        BeautifulSoupUtils.prettify_and_save(soup, path)


if __name__ == "__main__":
    main()
