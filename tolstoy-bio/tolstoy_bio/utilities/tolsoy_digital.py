from datetime import datetime
import re
from uuid import uuid4

import bs4

from tolstoy_bio.utilities.dates import RUSSIAN_FULL_MONTH_LABELS, RUSSIAN_FULL_MONTH_LABELS_IN_GENETIVE_CASE, Date
from tolstoy_bio.utilities.io import IoUtils
from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils


class TolstoyDigitalUtils:


    @classmethod
    def check_if_two_dates_have_two_week_gap_or_more(cls, iso_date_1: str, iso_date_2: str) -> bool:
        if iso_date_1 == iso_date_2 and cls.check_if_date_has_no_day(iso_date_1):
            return True

        date_1 = datetime.fromisoformat(iso_date_1)
        date_2 = datetime.fromisoformat(iso_date_2)
        delta = date_2 - date_1

        return abs(delta.days) >= 14
    
    @staticmethod
    def check_if_date_has_no_day(iso_date):
        return bool(re.match(r"^\d{4}-\d{2}$", iso_date))
    
    @classmethod
    def get_period_label_given_two_dates(cls, iso_date_1: str, iso_date_2: str) -> str:
        if iso_date_1 == iso_date_2 and cls.check_if_date_has_no_day(iso_date_1):
            return "weekly"

        date_1 = datetime.fromisoformat(iso_date_1)
        date_2 = datetime.fromisoformat(iso_date_2)

        if date_1.year != date_2.year:
            return "yearly"
        elif date_1.month != date_2.month:
            return "monthly"
        else:
            return "weekly"
        
    @staticmethod
    def format_date_range(start_date_iso: str, end_date_iso: str) -> str:
        start_date = Date.from_tei_date(start_date_iso)

        if start_date_iso == end_date_iso:
            year = start_date.year
            day = start_date.day

            if day:
                month = RUSSIAN_FULL_MONTH_LABELS_IN_GENETIVE_CASE[start_date.month - 1]
                return f"{day} {month} {year}"
            else:
                month = RUSSIAN_FULL_MONTH_LABELS[start_date.month - 1].upper()
                return f"{month} {year}"
            
        end_date = Date.from_tei_date(end_date_iso)

        if start_date.year == end_date.year and start_date.month == end_date.month:
            month = RUSSIAN_FULL_MONTH_LABELS_IN_GENETIVE_CASE[start_date.month - 1]
            return f"{start_date.day}–{end_date.day} {month} {start_date.year}"
        
        if start_date.year == end_date.year and start_date.month != end_date.month:
            start_month = RUSSIAN_FULL_MONTH_LABELS_IN_GENETIVE_CASE[start_date.month - 1]
            end_month = RUSSIAN_FULL_MONTH_LABELS_IN_GENETIVE_CASE[end_date.month - 1]
            return f"{start_date.day} {start_month} — {end_date.day} {end_month} {start_date.year}"
    
        if start_date.year != end_date.year and start_date.month != end_date.month:
            start_month = RUSSIAN_FULL_MONTH_LABELS_IN_GENETIVE_CASE[start_date.month - 1]
            end_month = RUSSIAN_FULL_MONTH_LABELS_IN_GENETIVE_CASE[end_date.month - 1]
            return f"{start_date.day} {start_month} {start_date.year} — {end_date.day} {end_month} {end_date.year}"
        
        raise ValueError(f"Unexpected date range from {start_date_iso} to {end_date_iso}");

    @staticmethod
    def process_nested_paragraph_tags_inside_notes(document_soup: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
        stringified_soup = BeautifulSoupUtils.inline_prettify(document_soup)

        def process_paragraph_tags(match: re.Match):
            string = match.group()
            string = re.sub("<p .*?>|<p>", r"<span>", string)
            string = re.sub("</p>", r"</span><lb/>", string)
            return string

        stringified_soup = re.sub(r"<note .*?</note>", process_paragraph_tags, stringified_soup, flags=re.DOTALL)
        stringified_soup = re.sub(r"<lb/></note>", "</note>", stringified_soup)

        return bs4.BeautifulSoup(stringified_soup, "xml")

    @staticmethod
    def has_nested_paragraph_tags(soup: bs4.BeautifulSoup) -> bool:
        for p in soup.find_all("p"):
            if p.find("p"):
                return True
        
        return False
    
    @classmethod
    def add_unique_ids_to_paragraphs(cls, soup: bs4.BeautifulSoup) -> None:
        ps = soup.find_all("p")

        for p in ps:
            cls.add_unique_id_to_tag(p)

    @staticmethod
    def add_unique_id_to_tag(tag: bs4.Tag) -> None:
        tag.attrs["id"] = uuid4()
