import os

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils
from .record import Record
from .record_processor import RecordProcessor


TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.xml")


class FragmentProcessor:
    def __init__(self, source_path: str):
        self.source_path = source_path
        self.source_soup = BeautifulSoupUtils.create_soup_from_file(source_path, "xml")

    def convert_records_to_tei(self, saving_repository_path: str):
        records_elements = self.source_soup.find_all("_Records")
        
        records_entities = [
            Record(source_path=self.source_path, index=index, soup=soup)
            for index, soup in enumerate(records_elements)
        ]

        for record in records_entities:
            record_processor = RecordProcessor(record)
            record_processor.convert_to_tei()
            
            saving_path = os.path.join(saving_repository_path, f"{record_processor.get_record_id()}.xml")
            record_processor.format_and_save(saving_path)
