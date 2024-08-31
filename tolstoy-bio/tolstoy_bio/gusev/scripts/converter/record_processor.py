from copy import deepcopy
from functools import cached_property, lru_cache
import os
import re

import bs4

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils
from tolstoy_bio.utilities.io import IoUtils
from tolstoy_bio.utilities.dates import RUSSIAN_FULL_MONTH_LABELS_IN_GENETIVE_CASE, RUSSIAN_FULL_MONTH_LABELS_IN_GENETIVE_CASE_TO_MONTH_NUMBER
from .record import Record
from .date_elements_builder import DateElementsBuilder
from .date_elements_builder_2 import DateProcessor, Date, DateRange
from .record_id_manager import RecordIdManager


TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.xml")


class RecordDateParser:
    _record: Record

    def __init__(self, record: Record):
        self._record = record

    @cached_property
    def year_label(self) -> str:
        tag_name = "_Year"

        elements = self._record.soup.find_all(tag_name)
        assert len(elements) == 1, f"Unexpected number of <{tag_name}> elements: {len(elements)} - in {self.record.source_path} at position {self.record.index}"
        
        element = elements[0]
        return re.sub(r"\s+", " ", element.text.strip())
    
    @cached_property
    def date_label(self) -> str:
        tag_name = "_Date"

        elements = self._record.soup.find_all(tag_name)
        assert len(elements) == 1, f"Unexpected number of <{tag_name}> elements: {len(elements)} - in {self.record.source_path} at position {self.record.index}"
        
        element = elements[0]
        return re.sub(r"\s+", " ", element.text.strip())

    @cached_property
    def parsed_components(self):
        processor = DateProcessor(self.year_label, self.date_label)
        return processor.parse()
        
    def get_first_date_as_tei(self):
        dates = self.parsed_components.dates

        if not dates:
            return "0000-00-00"
        
        date = dates[0]
        
        match date:
            case Date():
                return date.to_tei()
            case DateRange(start_date=start_date):
                return start_date.to_tei()
            
    def get_last_date_as_tei(self):
        dates = self.parsed_components.dates

        if not dates:
            return "0000-00-00"
        
        date = dates[-1]
        
        match date:
            case Date():
                return date.to_tei()
            case DateRange(end_date=end_date):
                return end_date.to_tei()



class RecordProcessor:
    def __init__(self, record: Record, record_id_manager: RecordIdManager):
        self.record = record
        self.source_soup = deepcopy(record.soup)
        self.output_soup = BeautifulSoupUtils.create_soup_from_file(TEMPLATE_PATH, "xml")
        self.date_parser = RecordDateParser(record)
        self.record_id_manager = record_id_manager

    @cached_property
    def fragment_filename(self) -> str:
        return os.path.basename(self.record.source_path).replace(".xml", "")
    
    @cached_property
    def volume_number(self) -> str:
        match = re.search(r"Том_(\d+)", self.fragment_filename)
        assert match, f"Failed to parse a volume number from a filename: {self.fragment_filename}"
        return match.group(1)
    
    @cached_property
    def start_page_number(self) -> str:
        start_page_elements = self.source_soup.find_all("_StartPageNo")
        assert len(start_page_elements) == 1, f"Unexpected number of <_StartPageNo> elements: {len(start_page_elements)} - in {self.record.source_path} at position {self.record.index}"
        
        start_page_element = start_page_elements[0]
        start_page_text = start_page_element.text.strip()

        # TODO: обработать невалидные значения, например в "Данные_Том_2_Фрагмент_18.xml"
        if self.fragment_filename not in ["Данные_Том_2_Фрагмент_18", "Данные_Том_2_Фрагмент_19"]:
            assert re.match(r"^\d+$", start_page_text), f"Unexpected start page number format: {start_page_text} - in {self.record.source_path} at position {self.record.index}"

        return start_page_text
    
    @cached_property
    def end_page_number(self) -> str:
        end_page_elements = self.source_soup.find_all("_EndPageNo")
        assert len(end_page_elements) == 1, f"Unexpected number of <_EndPageNo> elements: {len(end_page_elements)} - in {self.record.source_path} at position {self.record.index}"
        
        end_page_element = end_page_elements[0]
        end_page_text = end_page_element.text.strip()
        assert re.match(r"^\d+$", end_page_text), f"Unexpected end page number format: {end_page_text} - in {self.record.source_path} at position {self.record.index}"

        return end_page_text
    
    @cached_property
    def year_label(self) -> str:
        tag_name = "_Year"

        elements = self.source_soup.find_all(tag_name)
        assert len(elements) == 1, f"Unexpected number of <{tag_name}> elements: {len(elements)} - in {self.record.source_path} at position {self.record.index}"
        
        element = elements[0]
        return re.sub(r"\s+", " ", element.text.strip())
    
    @cached_property
    def date_label(self) -> str:
        tag_name = "_Date"

        elements = self.source_soup.find_all(tag_name)
        assert len(elements) == 1, f"Unexpected number of <{tag_name}> elements: {len(elements)} - in {self.record.source_path} at position {self.record.index}"
        
        element = elements[0]
        return re.sub(r"\s+", " ", element.text.strip())

    @cached_property
    def document_id(self):
        # if True:
        #     fragment_name = os.path.basename(self.record.source_path).replace(".xml", "")
        #     return f"gusev_v1_{fragment_name}_{self.record.index}"
        
        components = [
            "gusev",
            f"v{self.volume_number}",
            str(self.start_page_number),
            str(self.end_page_number),
            self.date_parser.get_first_date_as_tei().replace("-", "_"),
            self.date_parser.get_last_date_as_tei().replace("-", "_"),
        ]

        return self.record_id_manager.generate_based_on("_".join(components)) 
    
    def convert_to_tei(self, saving_path: str) -> None:
        self._build_tei_stub()
        self._build_tei_header()
        self._format_and_save_tei(saving_path)

    def _build_tei_stub(self):
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

        # TODO: согласовать обработку случаев, где контент _Comment разделён на абзацы через пустую строку.
        comment_elements = self.source_soup.find_all("_Comment")
        assert len(comment_elements) == 1, f"Zero or more than one <_Comment> has been found in {self.record.source_path} at position {self.record.index}"
        if comment_elements:
            comment_element = deepcopy(comment_elements[0])
            comment_element.name = "note"
            comment_element.attrs = {"type": "comment"}
            tei_body.append(comment_element)

    def _build_tei_header(self) -> None:
        tei_header = self.output_soup.find("teiHeader")
        tei_header.clear()

        file_desc = self._build_file_desc()
        profile_desc = self._build_profile_desc()

        tei_header.append(file_desc)
        tei_header.append(profile_desc)

    def _build_file_desc(self) -> bs4.Tag:
        file_desc = self.output_soup.new_tag("fileDesc")
        title_stmt = self._build_title_stmt()
        source_desc = self._build_source_desc()

        file_desc.append(title_stmt)
        file_desc.append(source_desc)

        return file_desc
    
    def _build_title_stmt(self) -> bs4.Tag:
        title_stmt = self.output_soup.new_tag("titleStmt")

        main_title = self.output_soup.new_tag("title", attrs={'type': 'main'})
        main_title.append(self.output_soup.new_string("Гусев Н.Н. Летопись жизни и творчества Л.Н. Толстого"))
        title_stmt.append(main_title)

        id_title = self.output_soup.new_tag("title", attrs={'xml:id': self.document_id})
        title_stmt.append(id_title)

        bibl_title = self.output_soup.new_tag("title", attrs={'type': 'bibl'})
        bibl_title.append(self.output_soup.new_string("Гусев Н. Н. Летопись жизни и творчества Льва Николаевича Толстого: в 2 тт. М.: Гослитиздат, 1958–1960."))
        title_stmt.append(bibl_title)

        return title_stmt

    def _build_source_desc(self) -> bs4.Tag:
        source_desc = self.output_soup.new_tag("sourceDesc")

        bibl_struct = self._build_bibl_struct()
        related_item = self._build_related_item()

        source_desc.append(bibl_struct)
        source_desc.append(related_item)

        return source_desc
    
    def _build_bibl_struct(self) -> bs4.Tag:
        bibl_struct = self.output_soup.new_tag("biblStruct")

        analytic = self.output_soup.new_tag("analytic")
        bibl_struct.append(analytic)
        
        author = self.output_soup.new_tag("author")
        analytic.append(author)

        person = self.output_soup.new_tag("person", attrs={"ref": "4055"})
        person.append(self.output_soup.new_string("Николай Николаевич Гусев"))
        author.append(person)

        volume_bibl_scope = self.output_soup.new_tag("biblScope", attrs={"unit": "vol"})
        volume_bibl_scope.append(self.output_soup.new_string(self.volume_number))
        analytic.append(volume_bibl_scope)

        page_bibl_scope = self.output_soup.new_tag("biblScope", attrs={"unit": "page"})

        page_number_range = self.start_page_number if self.start_page_number == self.end_page_number else f"{self.start_page_number}-{self.end_page_number}"
        page_bibl_scope.append(self.output_soup.new_string(page_number_range))
        analytic.append(page_bibl_scope)

        return bibl_struct
    
    def _build_related_item(self) -> bs4.Tag:
        related_item = self.output_soup.new_tag("relatedItem")

        list_bibl = self.output_soup.new_tag("listBibl")
        related_item.append(list_bibl)

        source_tags = self.record.soup.find_all("_Source")
        assert len(source_tags) == 1, "More than one <_Source> tag found."
        source_tag = source_tags[0]
        source_tag_text = re.sub(r"\s+", " ", source_tag.text.strip())
        bibl_fragments = re.findall(r"<bibl>(.*?)</bibl>", source_tag_text)

        if bibl_fragments:
            for bibl_fragment in bibl_fragments:
                bibl = self.output_soup.new_tag("bibl")
                bibl.append(self.output_soup.new_string(bibl_fragment))
                list_bibl.append(bibl)
        else:
            bibl = self.output_soup.new_tag("bibl")
            bibl.append(self.output_soup.new_string("check"))
            list_bibl.append(bibl)

        return related_item
    
    def _build_profile_desc(self) -> None:
        profile_desc = self.output_soup.new_tag("profileDesc")
        
        text_class = self._build_text_class()
        creation = self._build_creation()

        profile_desc.append(text_class)
        profile_desc.append(creation)

        return profile_desc


    def _build_text_class(self) -> bs4.Tag:
        text_class = self.output_soup.new_tag("textClass")

        collection_cat_ref = self.output_soup.new_tag("catRef", attrs={
            "ana": "#collection",
            "target": "biodata",
        })

        literature_cat_ref = self.output_soup.new_tag("catRef", attrs={
            "ana": "#literature",
            "target": "biotopic",
        })

        text_class.append(collection_cat_ref)
        text_class.append(literature_cat_ref)

        return text_class
    
    def _build_creation(self) -> bs4.Tag:
        creation = self.output_soup.new_tag("creation")
        
        config = self.date_parser.parsed_components

        # TODO
        if config is None:
            return creation
        
        # editor date
        editor_date = self.output_soup.new_tag("date", attrs={"type": "editor"})
        editor_date.append(self.output_soup.new_string(config.editor_date_label))
        
        if any(date.is_uncertain for date in config.dates):
            self._add_uncertainty_attribute(editor_date)
        
        creation.append(editor_date)

        # calendar date
        for date in config.dates:
            calendar_date = self.output_soup.new_tag("date")

            match date:
                case Date():
                    calendar_date.attrs = {
                        "from": date.to_tei(),
                        "to": date.to_tei(),
                        "calendar": "TRUE",
                    }
                case DateRange(start_date=start_date, end_date=end_date):
                    calendar_date.attrs = {
                        "from": start_date.to_tei(),
                        "to": end_date.to_tei(),
                        "calendar": "FALSE" if date.is_two_weeks_long_or_longer else "TRUE",
                    }

                    if start_date.year != end_date.year:
                        calendar_date.attrs["period"] = "yearly"
                    elif start_date.month != end_date.month:
                        calendar_date.attrs["period"] = "monthly"
                    else:
                        calendar_date.attrs["period"] = "weekly"
            
            if date.is_uncertain:
                self._add_uncertainty_attribute(calendar_date)

            creation.append(calendar_date)

        raw_date = self.output_soup.new_tag("date", attrs={"type": "raw"})
        raw_date.append(self.output_soup.new_string(config.raw_date))
        creation.append(raw_date)

        encoded_date = self.output_soup.new_tag("date", attrs={"type": "code"})
        encoded_date.append(self.output_soup.new_string(config.date_pattern))
        creation.append(encoded_date)

        return creation

    def _add_uncertainty_attribute(self, tag: bs4.Tag) -> None:
        tag.attrs["cert"] = "low"

    def _format_and_save_tei(self, path: str) -> None:
        content = self.output_soup.prettify()
        IoUtils.save_textual_data(content, path)
