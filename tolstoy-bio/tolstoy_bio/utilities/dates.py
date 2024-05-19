from dataclasses import dataclass
import re

from tolstoy_bio.utilities.number import NumberUtils


RUSSIAN_FULL_MONTH_LABELS_IN_GENETIVE_CASE = [
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря"
]

RUSSIAN_FULL_MONTH_LABELS_IN_GENETIVE_CASE_TO_MONTH_NUMBER = {
    "января": 1,
    "февраля": 2,
    "марта": 3,
    "апреля": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "августа": 8,
    "сентября": 9,
    "октября": 10,
    "ноября": 11,
    "декабря": 12,
}

ROMAN_NUMERAL_REGEX_STRING = r'M{0,3}(CM|CD|D?C{0,3})?(XC|XL|L?X{0,3})?(IX|IV|V?I{0,3})?'

@dataclass
class Date:
    year: int = None
    month: int = None
    day: int = None

    def to_iso(self) -> str | None:
        if self.year and self.month and self.day:
            return self._to_date_iso()
        
        if self.year and self.month:
            return self._to_month_iso()
        
        if self.year:
            return self._to_year_iso()
        
        return None

    def _to_date_iso(self):
        month_iso = self._to_month_iso()
        return f"{month_iso}-{self._pad_number_to_two_digits(self.day)}"
    
    def _to_month_iso(self):
        year_iso = self._to_year_iso()
        return f"{year_iso}-{self._pad_number_to_two_digits(self.month)}"
    
    def _to_year_iso(self):
        return str(self.year)
    
    @staticmethod
    def _pad_number_to_two_digits(number: int):
        return str(number).zfill(2)

russian_full_day_month_label_pattern = re.compile(
    rf"(\d+|({ROMAN_NUMERAL_REGEX_STRING}))\s+({'|'.join(RUSSIAN_FULL_MONTH_LABELS_IN_GENETIVE_CASE)})",
    flags=re.IGNORECASE
)

class DateUtils:
    @staticmethod
    def get_russian_full_month_labels_in_genetive_case() -> list[str]:
        return RUSSIAN_FULL_MONTH_LABELS_IN_GENETIVE_CASE
    
    @classmethod
    def convert_russian_day_month_label_to_date(cls, label: str) -> Date | None:
        russian_full_day_month_label_pattern = re.compile(
            rf"(\d+|({ROMAN_NUMERAL_REGEX_STRING}))\s+({'|'.join(RUSSIAN_FULL_MONTH_LABELS_IN_GENETIVE_CASE)})",
            flags=re.IGNORECASE
        )

        match = russian_full_day_month_label_pattern.match(label)
        
        if not match:
            return None
        
        day_label, *_, month_label = match.groups()

        month_number = cls.get_month_number_by_russian_genetive_label(month_label)
        day_number = int(day_label) if day_label.isnumeric() else NumberUtils.convert_roman_numeral_to_number(day_label)

        if not day_number:
            return None
        
        return Date(month=month_number, day=day_number)
    
    @staticmethod
    def get_month_number_by_russian_genetive_label(label: str):
        return RUSSIAN_FULL_MONTH_LABELS_IN_GENETIVE_CASE_TO_MONTH_NUMBER[
            label.strip().lower()
        ]