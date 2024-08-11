from copy import deepcopy
import os

import bs4

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils
from tolstoy_bio.utilities.io import IoUtils
from .record import Record


TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.xml")


class RecordProcessor:
    def __init__(self, record: Record):
        self.record = record
        self.source_soup = deepcopy(record.soup)
        self.output_soup = BeautifulSoupUtils.create_soup_from_file(TEMPLATE_PATH, "xml")

    def convert_to_tei(self) -> None:
        tei_header = self.output_soup.find("teiHeader")
        tei_body = self.output_soup.find("text").find("body")

        year_elements = self.source_soup.find_all("_Year")
        assert len(year_elements) == 1, f"Unexpected number of <_Year> elements: {len(year_elements)}"
        year_element = year_elements[0]
        tei_header.append(deepcopy(year_element))

        date_elements = self.source_soup.find_all("_Date")
        assert len(date_elements) == 1, f"Unexpected number of <_Date> elements: {len(date_elements)}"
        date_element = date_elements[0]
        tei_header.append(deepcopy(date_element))

        start_page_elements = self.source_soup.find_all("_StartPageNo")
        assert len(start_page_elements) == 1, f"Unexpected number of <_StartPageNo> elements: {len(start_page_elements)}"
        start_page_element = start_page_elements[0]
        tei_header.append(deepcopy(start_page_element))

        end_page_elements = self.source_soup.find_all("_EndPageNo")
        assert len(end_page_elements) == 1, f"Unexpected number of <_EndPageNo> elements: {len(end_page_elements)}"
        end_page_element = end_page_elements[0]
        tei_header.append(deepcopy(end_page_element))

        source_elements = self.source_soup.find_all("_Source")
        assert len(source_elements) == 1, f"Unexpected number of <_Source> elements: {len(source_elements)}"
        source_element = source_elements[0]
        tei_header.append(deepcopy(source_element))

        comment_elements = self.source_soup.find_all("_Comment")
        assert len(comment_elements) == 1, f"Zero or more than one <_Comment> has been found in {self.record.source_path} at position {self.record.index}"
        if comment_elements:
            comment_element = deepcopy(comment_elements[0])
            comment_element.name = "note"
            comment_element.attrs = {"type": "comment"}
            tei_body.append(comment_element)

    def get_record_id(self):
        fragment_name = os.path.basename(self.record.source_path).replace(".xml", "")
        return f"gusev_v1_{fragment_name}_{self.record.index}"

    def format_and_save(self, path: str) -> None:
        content = self.output_soup.prettify()
        IoUtils.save_textual_data(content, path)
