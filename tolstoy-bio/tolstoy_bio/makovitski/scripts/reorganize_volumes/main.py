from collections import Counter
from dataclasses import dataclass
import os

import bs4

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils
from tolstoy_bio.utilities.io import IoUtils

from .configs import get_volumes_configs, VolumeBuildingConfig


class YearDocumentContentExtractor:
    _soup: bs4.BeautifulSoup
    _id: str

    def __init__(self, path: str):
        self._soup = BeautifulSoupUtils.create_soup_from_file(path, "xml")
        self._id = self._extract_id(self._soup)

    def _extract_id(self, soup: bs4.BeautifulSoup):
        return soup.find("title", attrs={"xml:id": True}).attrs["xml:id"]
    
    def extract_as_div(self) -> bs4.BeautifulSoup:
        self._remove_header()
        self._unwrap_text_divisions()
        self._unwrap_month_divisions()
        self._move_date_attributes_from_dates_to_entries()
        self._remove_ids_from_refs()
        self._make_ids_global()

        body = self._extract_body()
        body.name = "div"
        body.attrs = {"type": "year"}

        self._move_date_attributes_from_head_to_year()

        return body    

    def _remove_header(self):
        self._soup.find("teiHeader").decompose()

    def _unwrap_text_divisions(self):
        for element in self._soup.find_all("div", attrs={"type": "text"}):
            element.unwrap()

    def _unwrap_month_divisions(self):
        for element in self._soup.find_all("div", attrs={"type": "month"}):
            element.unwrap()

    def _move_date_attributes_from_dates_to_entries(self):
        entries = self._soup.find_all("div", attrs={"type": "entry"})

        for element in entries:
            date = element.find("date")
            element.attrs.update(date.attrs)
            date.unwrap()

            if "when" in element.attrs:
                element.attrs["date"] = element.attrs["when"]
                del element.attrs["when"]

    def _remove_ids_from_refs(self):
        refs = self._soup.find_all("ref", attrs={"target": True, "xml:id": True})

        for element in refs:
            del element.attrs['xml:id']

    def _make_ids_global(self):
        xml_id_elements = self._soup.find_all(attrs={"xml:id": True})

        for element in xml_id_elements:
            element_id = element.attrs["xml:id"]
            element.attrs["xml:id"] = self._build_global_element_id(element_id)

        assert len(xml_id_elements) == len(set([e.attrs["xml:id"] for e in xml_id_elements])), f"Repeated @xml:id found. {Counter([e.attrs['xml:id'] for e in xml_id_elements])}"

        refs = self._soup.find_all("ref", attrs={"target": True})

        for element in refs:
            element_id = element.attrs["target"]
            element_updated_id = self._build_global_element_id(element_id.strip("#"))
            element.attrs["target"] = f"#{element_updated_id}" if element_id.startswith("#") else element_updated_id
        
    def _build_global_element_id(self, element_id: str) -> str:
        if not element_id:
            return element_id
        
        return f"{self._id}__${element_id}"
    
    def _extract_body(self):
        bodies = self._soup.find_all("body")
        assert len(bodies) == 1, "More than one body found."
        return bodies[0]
    
    def _move_date_attributes_from_head_to_year(self):
        date = self._soup.find("head").find("date")
        body = self._soup.find("div", {"type": "year"})

        body.attrs.update(date.attrs)
        date.unwrap()

        if "when" in body.attrs:
            body.attrs["date"] = body.attrs["when"]
            del body.attrs["when"]


class VolumeBuilder:
    _config: VolumeBuildingConfig
    _volume_soup: bs4.BeautifulSoup

    def __init__(self, config: VolumeBuildingConfig):
        self._config = config
        self._volume_soup = self._initiate_volume_soup()
    
    @staticmethod
    def _initiate_volume_soup() -> bs4.BeautifulSoup:
        module_folder_path = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(module_folder_path, "template.xml")
        return BeautifulSoupUtils.create_soup_from_file(template_path, "xml")
    
    def build(self, target_repository_path: str):
        self._add_xml_id()
        self._add_title()
        self._add_main_title()
        self._add_bibl_title()
        self._add_start_date()
        self._add_end_date()
        self._add_editor_date()
        self._add_body()
        self._save(target_repository_path)

    def _add_xml_id(self):
        element = self._volume_soup.find("title", {"xml:id": True})
        element.attrs["xml:id"] = self._config.volume_id
    
    def _add_title(self):
        element = self._volume_soup.find("title")
        BeautifulSoupUtils.set_inner_text(element, self._config.title)
    
    def _add_main_title(self):
        element = self._volume_soup.find("title", {"type": "main"})
        BeautifulSoupUtils.set_inner_text(element, self._config.main_title)

    def _add_bibl_title(self):
        element = self._volume_soup.find("title", {"type": "bibl"})
        BeautifulSoupUtils.set_inner_text(element, self._config.bibl_title)

    def _add_start_date(self):
        element = self._volume_soup.find("date", {"calendar": True})
        element.attrs["from"] = self._config.from_date

    def _add_end_date(self):
        element = self._volume_soup.find("date", {"calendar": True})
        element.attrs["to"] = self._config.to_date

    def _add_editor_date(self):
        element = self._volume_soup.find("date", {"type": "editor"})
        BeautifulSoupUtils.set_inner_text(element, self._config.editor_date)

    def _add_body(self):
        for subvolume_id in self._config.subvolumes_ids:
            subvolume_path = self._get_subvolume_path(subvolume_id)
            subvolume_extractor = YearDocumentContentExtractor(subvolume_path)
            segment = subvolume_extractor.extract_as_div()
            self._volume_soup.find("body").append(segment)

    def _get_subvolume_path(self, submodule_id: str) -> str:
        module_folder_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(module_folder_path, f"../../data/xml/by_year/{submodule_id}.xml")
    
    def _save(self, folder_path: str):
        filename = f"{self._config.volume_id}.xml"
        filepath = os.path.join(folder_path, filename)
        IoUtils.save_textual_data(self._volume_soup.prettify(), filepath)


def main():
    module_folder_path = os.path.dirname(os.path.abspath(__file__))
    target_repository_path = os.path.join(module_folder_path, "../../data/xml/by_volume")

    volumes_configs = get_volumes_configs()

    for config in volumes_configs:
        builder = VolumeBuilder(config)
        builder.build(target_repository_path)


if __name__ == "__main__":
    main()
