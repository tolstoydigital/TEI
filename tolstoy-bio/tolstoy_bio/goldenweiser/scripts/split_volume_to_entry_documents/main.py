from copy import deepcopy
import os
from pprint import pprint

import bs4

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils
from tolstoy_bio.utilities.io import IoUtils
from tolstoy_bio.goldenweiser.scripts.document_name_generator import get_goldenweiser_document_name_generator
from tolstoy_bio.goldenweiser.scripts.split_volume_to_entry_documents.entry_template import get_entry_template


VOLUME_PATH = os.path.abspath(os.path.join(__file__, '../../../data/xml/goldenweiser-diaries_1896_1910.xml'))
ENTRIES_FOLDER_PATH = os.path.abspath(os.path.join(__file__, '../../../data/xml/by_entry'))


class GoldenweiserVolumeSplitter:
    _ENTRY_START_MARKER_LABEL = "entryStart"
    _ENTRY_END_MARKER_LABEL = "entryEnd"

    def __init__(self, content: str):
        self._soup = self._build_soup_from_content(content)

    @staticmethod
    def _build_soup_from_content(content: str) -> bs4.BeautifulSoup:
        return bs4.BeautifulSoup(content, "xml")

    @classmethod
    def from_path(cls, path: str):
        content = IoUtils.read_as_text(path)
        return cls(content)
    
    def get_formatted_content():
        return 
    
    def split(self, folder_path_to_save: str):
        _, *datelines = self._soup.find_all("dateline")

        for index, dateline in enumerate(datelines):
            paragraph = BeautifulSoupUtils.get_closest_ancestor_with_tag_name(dateline, "p")

            if index > 0:
                paragraph.insert_before(self._create_entry_end_marker())

            paragraph.insert_before(self._create_entry_start_marker())

        appendix_paragraph = self._get_appendix_paragraph()
        appendix_paragraph.insert_before(self._create_entry_end_marker())

        inline_soup = BeautifulSoupUtils.inline_prettify(self._soup)
        inline_soup = inline_soup.replace(f"<{self._ENTRY_START_MARKER_LABEL}/>", '<div type="entry">')
        inline_soup = inline_soup.replace(f"<{self._ENTRY_END_MARKER_LABEL}/>", '</div>')

        self._soup = self._build_soup_from_content(inline_soup)
        # IoUtils.save_textual_data(self._soup.prettify(), VOLUME_PATH)
        
        entries = self._soup.find_all("div", attrs={"type": "entry"})

        print(len(entries), 'entries found')

        document_name_generator = get_goldenweiser_document_name_generator()

        for entry in entries:
            years = entry.find_all("year")
            assert len(years) < 2, "More years than expected in an entry"
            
            if years:
                year = years[0]

                if entry.find("opener").find("year") is year:
                    year.unwrap()
                else:
                    year.decompose()

            date = entry.find("dateline").find("date").attrs.get("when", None)
            assert date, "Failed to parse date in an entry"
            document_name = document_name_generator.generate(date)

            entry_template = get_entry_template(
                document_id=document_name.to_string(),
                date=date
            )

            entry_soup = self._build_soup_from_content(entry_template)
            entry_soup.find("text").find("body").extend(deepcopy(entry).contents)
            entry_path = os.path.join(folder_path_to_save, document_name.to_filename("xml"))
            IoUtils.save_textual_data(entry_soup.prettify(), entry_path)

    def _create_entry_start_marker(self):
        return self._soup.new_tag(self._ENTRY_START_MARKER_LABEL)
    
    def _create_entry_end_marker(self):
        return self._soup.new_tag(self._ENTRY_END_MARKER_LABEL)
    
    def _get_appendix_paragraph(self):
        heads = self._soup.find_all("head")

        for head in heads:
            if head.text.strip() == "Приложения":
                return BeautifulSoupUtils.get_closest_ancestor_with_tag_name(head, "p")
        
        raise AssertionError("Failed to find 'appendix' paragraph.")


def main():
    splitter = GoldenweiserVolumeSplitter.from_path(VOLUME_PATH)
    splitter.split(ENTRIES_FOLDER_PATH)


if __name__ == '__main__':
    main()