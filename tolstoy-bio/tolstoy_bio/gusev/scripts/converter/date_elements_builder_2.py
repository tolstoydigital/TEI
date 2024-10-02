import calendar
from dataclasses import dataclass, fields
from datetime import datetime, timedelta
from enum import StrEnum
from functools import cached_property
from itertools import groupby
import math
from pprint import pprint
import re
from typing import Callable

from tolstoy_bio.utilities.dates import RUSSIAN_FULL_MONTH_LABELS, RUSSIAN_FULL_MONTH_LABELS_IN_GENETIVE_CASE

# Numerical bounds for the start, middle and end of a month
MONTH_START_LAST_DAY = 10
MONTH_MIDDLE_FIRST_DAY = 11
MONTH_MIDDLE_LAST_DAY = 20
MONTH_END_FIRST_DAY = 21

# Union regex pattern for Russian month labels in genitive and nominative cases
base_month_pattern = f"{'|'.join([*RUSSIAN_FULL_MONTH_LABELS_IN_GENETIVE_CASE, *RUSSIAN_FULL_MONTH_LABELS])}"


def get_genitive_month(month: int):
    return RUSSIAN_FULL_MONTH_LABELS_IN_GENETIVE_CASE[month - 1]


def get_nominative_month(month: int):
    return RUSSIAN_FULL_MONTH_LABELS[month - 1]


class Date:
    """
    Generic date builder.
    Supports date decoding from Russian labels.
    Supports date encoding to TEI format and localized label.
    """

    year: int
    month: int | None
    day: int | None
    is_uncertain: bool = False
    is_around: bool = False

    def __init__(self, 
                 year: str | int, 
                 month: str | int | None = None, 
                 day: str | int | None = None,
                 is_uncertain: bool = False
                 ):
        self.year = self._encode_year(year)
        self.month = self._encode_month(month)

        if day is None:
            self.day = None
        elif int(day) == 37:
            self.day = 31
        else:
            self.day = int(day)

        self.is_uncertain = is_uncertain

        if self.month is None and self.day is not None:
            raise ValueError("The day is known, but the month is not.")

    @classmethod
    def first_day_in_month(cls, year, month):
        year = cls._encode_year(year)
        month = cls._encode_month(month)
        return cls(year, month, 1)
    
    @classmethod
    def middle_day_in_month(cls, year, month):
        year = cls._encode_year(year)
        month = cls._encode_month(month)
        _, last_day = calendar.monthrange(year, month)
        middle_day = math.ceil((last_day - 1) / 2)
        return cls(year, month, middle_day)
    
    @classmethod
    def last_day_in_month(cls, year, month):
        year = cls._encode_year(year)
        month = cls._encode_month(month)
        _, day = calendar.monthrange(year, month)
        return cls(year, month, day)
    

    
    @classmethod
    def first_day_in_year(cls, year):
        return cls(
            year=cls._encode_year(year), 
            month=1, 
            day=1
        )
    
    @classmethod
    def last_day_in_year(cls, year):
        return cls(
            year=cls._encode_year(year), 
            month=12, 
            day=31
        )

    @staticmethod
    def _encode_year(value: str | int):
        if type(value) is int:
            return value
        
        if type(value) is str and value.isnumeric():
            return int(value)
        
        raise NotImplementedError(f"Unexpected year format: {value}")
        
    @staticmethod
    def _encode_month(value: str | int | None):
        if value is None:
            return None
        
        if type(value) is int:
            return value
        
        if type(value) is not str:
            raise NotImplementedError(f"Unexpected month format: {value}")

        if value.isnumeric():
            return int(value)
        
        if value.lower() in RUSSIAN_FULL_MONTH_LABELS_IN_GENETIVE_CASE:
            return RUSSIAN_FULL_MONTH_LABELS_IN_GENETIVE_CASE.index(value.lower()) + 1
        
        if value.lower() in RUSSIAN_FULL_MONTH_LABELS:
            return RUSSIAN_FULL_MONTH_LABELS.index(value.lower()) + 1
            
        raise NotImplementedError(f"Unexpected month format: '{value}'")
        
    def to_tei(self) -> str:
        components = [self.year, self.month, self.day]
        components = [str(component).zfill(2) if component else "" for component in components]
        return "-".join(components).strip("-")
    
    def to_local_string(self) -> str:
        if self.day:
            month_label = RUSSIAN_FULL_MONTH_LABELS_IN_GENETIVE_CASE[self.month - 1]
            return f"{self.day} {month_label} {self.year} года"
        
        if self.month:
            month_label = RUSSIAN_FULL_MONTH_LABELS[self.month - 1]
            return f"{month_label} {self.year} года"
        
        return f"{self.year} год"
    
    def to_editor_format(self) -> str:
        if not self.day:
            raise ValueError("Failed to format the date because the day is not present.")
        
        if self.is_around:
            month_label = RUSSIAN_FULL_MONTH_LABELS_IN_GENETIVE_CASE[self.month - 1]
            day_label = f"{self.day} (?)" if self.is_uncertain else f"{self.day}"
            return f"около {day_label} {month_label} {self.year} года"
        
        month_label = RUSSIAN_FULL_MONTH_LABELS_IN_GENETIVE_CASE[self.month - 1]
        day_label = f"{self.day} (?)" if self.is_uncertain else f"{self.day}"
        return f"{day_label} {month_label} {self.year} года"
    
    @property
    def is_month(self):
        return self.month is not None and self.day is None
    
    @property
    def is_year(self):
        return self.month is not None
    
    @property
    def is_full(self) -> bool:
        return all(value is not None for value in [self.year, self.month, self.day])


class MonthPartLabel(StrEnum):
    START = "начало"
    MIDDLE = "середина"
    END = "конец"


@dataclass
class DateRange:
    """
    Generic date range.
    Supports date encoding to localized label.
    """

    start_date: Date
    end_date: Date
    _is_uncertain: bool = None
    is_start_of_month: bool = False
    is_middle_of_month: bool = False
    is_end_of_month: bool = False
    is_first_half_of_month: bool = False
    is_last_half_of_month: bool = False
    is_year: bool = False
    is_month: bool = False
    is_summer: bool = False
    is_autumn: bool = False
    before_label: str = ""
    after_label: str = ""
    is_night: bool = False
    is_year_range: bool = False
    part: MonthPartLabel = None
    part_range: tuple[MonthPartLabel, MonthPartLabel] = None

    @property
    def is_uncertain(self):
        if self._is_uncertain is None:
            return self.start_date.is_uncertain or self.end_date.is_uncertain
        
        return self._is_uncertain
    
    @is_uncertain.setter
    def is_uncertain(self, value):
        self._is_uncertain = value

    @property
    def is_two_weeks_long_or_longer(self):
        if self.start_date.day is None or self.end_date.day is None:
            return True
        
        if self.start_date.month is None or self.end_date.month is None:
            return True
        
        datetime_1 = datetime(self.start_date.year, self.start_date.month, self.start_date.day)
        datetime_2 = datetime(self.end_date.year, self.end_date.month, self.end_date.day)
        delta = abs(datetime_2 - datetime_1)
        return delta >= timedelta(days=14)
    
    @classmethod
    def start_of_month(cls, year, month, is_uncertain=False):
        start_date = Date.first_day_in_month(year, month)
        end_date = Date(year, month, MONTH_START_LAST_DAY)
        range = DateRange(start_date, end_date, is_uncertain)
        range.part = MonthPartLabel.START
        return range
    
    @classmethod
    def middle_of_month(cls, year, month, is_uncertain=False):
        start_date = Date(year, month, MONTH_MIDDLE_FIRST_DAY)
        end_date = Date(year, month, MONTH_MIDDLE_LAST_DAY)
        range = DateRange(start_date, end_date, is_uncertain)
        range.part = MonthPartLabel.MIDDLE
        return range

    @classmethod
    def end_of_month(cls, year, month, is_uncertain=False):
        start_date = Date(year, month, MONTH_END_FIRST_DAY)
        end_date = Date.last_day_in_month(year, month)
        range = DateRange(start_date, end_date, is_uncertain)
        range.part = MonthPartLabel.END
        return range
    
    @classmethod
    def first_half_of_month(cls, year, month):
        start_date = Date.first_day_in_month(year, month)
        end_date = Date.middle_day_in_month(year, month)
        range = DateRange(start_date, end_date)
        range.is_first_half_of_month = True
        return range
    
    @classmethod
    def last_half_of_month(cls, year, month):
        start_date = Date.middle_day_in_month(year, month)
        end_date = Date.middle_day_in_month(year, month)
        range = DateRange(start_date, end_date)
        range.is_last_half_of_month = True
        return range
    
    @classmethod
    def year(cls, year):
        start_date = Date.first_day_in_year(year)
        end_date = Date.last_day_in_year(year)
        range = DateRange(start_date, end_date)
        range.is_year = True
        return range
    
    @classmethod
    def month(cls, year, month):
        start_date = Date.first_day_in_month(year, month)
        end_date = Date.last_day_in_month(year, month)
        range = DateRange(start_date, end_date)
        range.is_month = True
        return range
    
    @classmethod
    def summer(cls, year):
        start_date = Date.first_day_in_month(year, 6)
        end_date = Date.last_day_in_month(year, 8)
        range = DateRange(start_date, end_date)
        range.is_summer = True
        return range
    
    @classmethod
    def autumn(cls, year):
        start_date = Date.first_day_in_month(year, 9)
        end_date = Date.last_day_in_month(year, 11)
        range = DateRange(start_date, end_date)
        range.is_autumn = True
        return range
    
    def to_editor_format(self) -> str:
        if self.part_range:
            if self.after_label:
                day_label = f"{self.start_date.day}?" if self.is_uncertain else self.start_date.day
                month_label = get_genitive_month(self.start_date.month)
                year_label = self.start_date.year
                return f"{self.part_range[0]} – {self.part_range[1]} {month_label} {year_label} года, {self.after_label} {day_label} {month_label}"
            elif self.before_label:
                day_label = f"{self.end_date.day}?" if self.is_uncertain else self.end_date.day
                month_label = get_genitive_month(self.end_date.month)
                year_label = self.end_date.year
                return f"{self.part_range[0]} – {self.part_range[1]}, {month_label} {year_label} года, {self.before_label} {day_label} {month_label}"
            else:
                month_label = get_genitive_month(self.start_date.month)
                year_label = self.start_date.year
                return f"{self.part_range[0]} – {self.part_range[1]} {month_label} {year_label} года"

        if self.part:
            if self.after_label:
                day_label = f"{self.start_date.day}?" if self.is_uncertain else self.start_date.day
                month_label = get_genitive_month(self.start_date.month)
                year_label = self.start_date.year
                return f"{self.part} {month_label} {year_label} года, {self.after_label} {day_label} {month_label}"
            elif self.before_label:
                day_label = f"{self.end_date.day}?" if self.is_uncertain else self.end_date.day
                month_label = get_genitive_month(self.end_date.month)
                year_label = self.end_date.year
                return f"{self.part} {month_label} {year_label} года, {self.before_label} {day_label} {month_label}"
            else:
                month_label = get_genitive_month(self.start_date.month)
                year_label = self.start_date.year
                return f"{self.part} {month_label} {year_label} года"
        
        if self.is_first_half_of_month:
            month_label = get_genitive_month(self.start_date.month)
            year_label = self.start_date.year
            return f"первая половина {month_label} {year_label} года"
        
        if self.is_last_half_of_month:
            month_label = get_genitive_month(self.start_date.month)
            year_label = self.start_date.year
            return f"вторая половина {month_label} {year_label} года"
        
        if self.is_year:
            year_label = f"{self.start_date.year}?" if self.is_uncertain else self.start_date.year
            return f"{year_label} год"
        
        if self.is_month:
            month_label = get_nominative_month(self.start_date.month)
            year_label = self.start_date.year
            return f"{month_label} {year_label} года"
        
        if self.is_summer:
            year_label = self.start_date.year
            return f"лето {year_label} года"
        
        if self.is_autumn:
            year_label = self.start_date.year
            return f"осень {year_label} года"
        
        if self.before_label:
            if self.start_date.year != self.end_date.year:
                raise ValueError("Unexpectedly different years in BeforeLabel type.")
            
            if self.start_date.day is None or self.end_date.day is None:
                raise ValueError("One of range bound doesn't have a day in BeforeLabel type.")

            if self.start_date.month == self.end_date.month:
                day_label = f"{self.end_date.day}?" if self.is_uncertain else self.end_date.day
                month_label = get_genitive_month(self.end_date.month)
                year_label = self.end_date.year
                return f"{self.before_label} {day_label} {month_label} {year_label} года"
            else:
                start_day = f"{self.start_date.day}?" if self.start_date.is_uncertain else self.start_date.day
                start_month_label = get_genitive_month(self.start_date.month)
                end_day = f"{self.end_date.day}?" if self.end_date.is_uncertain else self.end_date.day
                end_month_label = get_genitive_month(self.end_date.month)
                year_label = self.start_date.year
                return f"{start_day} {start_month_label} — {self.before_label} {end_day} {end_month_label} {year_label} года"
            
        if self.after_label:
            if self.start_date.year != self.end_date.year:
                raise ValueError("Unexpectedly different years in AfterLabel type.")
            
            if self.start_date.day is None or self.end_date.day is None:
                raise ValueError("One of range bound doesn't have a day in AfterLabel type.")

            if self.start_date.month == self.end_date.month:
                day_label = f"{self.start_date.day}?" if self.is_uncertain else self.start_date.day
                month_label = get_genitive_month(self.start_date.month)
                year_label = self.start_date.year
                return f"{self.after_label} {day_label} {month_label} {year_label} года"
            else:
                start_day = f"{self.start_date.day}?" if self.start_date.is_uncertain else self.start_date.day
                start_month_label = get_genitive_month(self.start_date.month)
                end_day = f"{self.end_date.day}?" if self.end_date.is_uncertain else self.end_date.day
                end_month_label = get_genitive_month(self.end_date.month)
                year_label = self.start_date.year
                return f"{self.after_label} {start_day} {start_month_label} — {end_day} {end_month_label} {year_label} года"
            
        if self.is_night:
            if self.start_date.year != self.end_date.year or self.start_date.month != self.end_date.month:
                raise NotImplementedError("Night range is across different months or years")

            start_day = f"{self.start_date.day}?" if self.start_date.is_uncertain else self.start_date.day
            end_day = f"{self.end_date.day}?" if self.end_date.is_uncertain else self.end_date.day
            month_label = get_genitive_month(self.start_date.month)
            year_label = self.start_date.year
            return f"ночь с {start_day} на {end_day} {month_label} {year_label} года"
        
        if self.is_year_range:
            start_year_label = f"{self.start_date.year}?" if self.start_date.is_uncertain else self.start_date.year
            end_year_label = f"{self.end_date.year}?" if self.end_date.is_uncertain else self.end_date.year
            return f"{start_year_label}–{end_year_label} год"
        
        if self.start_date.year != self.end_date.year:
            formatted_start_date = self.start_date.to_editor_format()
            formatted_end_date = self.start_date.to_editor_format()
            return f"{formatted_start_date} — {formatted_end_date}"
        
        if self.start_date.month != self.end_date.month:
            start_day = f"{self.start_date.day}?" if self.start_date.is_uncertain else self.start_date.day
            start_month_label = get_genitive_month(self.start_date.month)
            end_day = f"{self.end_date.day}?" if self.end_date.is_uncertain else self.end_date.day
            end_month_label = get_genitive_month(self.end_date.month)
            year_label = self.start_date.year
            return f"{start_day} {start_month_label} — {end_day} {end_month_label} {year_label} года"
        
        if self.start_date.day != self.end_date.day:
            start_day = f"{self.start_date.day}?" if self.start_date.is_uncertain else self.start_date.day
            end_day = f"{self.end_date.day}?" if self.end_date.is_uncertain else self.end_date.day
            month_label = get_genitive_month(self.start_date.month)
            year_label = self.start_date.year
            return f"{start_day}–{end_day} {month_label} {year_label} года"
        
        if self.start_date.day == self.end_date.day:
            return self.start_date.to_editor_format()
            
        raise NotImplementedError("Failed to build an editor format for the unexpected date range type.")


def delete_all_occurrences_except_last(string, substrings):
    for substring in substrings:
        occurrences = [m.start() for m in re.finditer(re.escape(substring), string)]
        
        if len(occurrences) > 1:
            delete_count = 0
            for occurrence in occurrences[:-1]:
                offset = occurrence - delete_count
                string = string[:offset] + string[offset + len(substring):]
                delete_count += len(substring)
    
    return string


def date_sequence_to_editor_format(dates: list[Date | DateRange], raw: str = "", convert_ranges=False) -> str:
    if any(
        range.start_date.year != range.end_date.year 
        for range in dates if isinstance(range, DateRange)
    ):
        raise NotImplementedError("Date sequence formatting is not implemented for the cases with ranges across different years.")

    def retrieve_year(date: list[Date | DateRange]) -> int:
        match date:
            case Date(year=year):
                return year
            case DateRange(start_date=start_bound, end_date=end_bound) if start_bound.year == end_bound.year:
                return start_bound.year
            case _:
                raise NotImplementedError("Date sequence formatting is not implemented for the cases with ranges across different years.")

    dates_sorted_by_year = sorted(dates, key=retrieve_year)
    dates_by_year = groupby(dates_sorted_by_year, key=retrieve_year)

    formatted_years = []

    for year, year_dates in dates_by_year:
        year_dates: list[Date | DateRange] = list(year_dates)
        year_label = f"{year} года"
        
        formatted_year_dates = [date.to_editor_format() for date in year_dates]
        joined_formatted_year_dates = ", ".join(formatted_year_dates)
        raw_formatted_year = f"{joined_formatted_year_dates} {year_label}"

        formatted_year = delete_all_occurrences_except_last(
            raw_formatted_year, 
            [
                f" {value}" for value in [
                    year_label,
                    *RUSSIAN_FULL_MONTH_LABELS_IN_GENETIVE_CASE,
                    *RUSSIAN_FULL_MONTH_LABELS,
                ]
            ]
        )

        if convert_ranges:
            if formatted_year.count("—") == 1:
                first_bound, second_bound = re.split(r"\s*—\s*", formatted_year)

                if match := re.match(rf"1 ({base_month_pattern})", first_bound):
                    genitive_month_label = match.group(1)
                    month_number = Date._encode_month(genitive_month_label)
                    nominative_month_label = RUSSIAN_FULL_MONTH_LABELS[month_number - 1]
                    first_bound = re.sub(match.group(), nominative_month_label, first_bound, 1)
                elif (match := re.match(rf"{MONTH_MIDDLE_FIRST_DAY} ({base_month_pattern})", first_bound)) and "середина" in raw:
                    first_bound = re.sub(match.group(), f"середина {match.group(1)}", first_bound, 1)
                elif (match := re.match(rf"{MONTH_END_FIRST_DAY} ({base_month_pattern})", first_bound)) and "конец" in raw:
                    first_bound = re.sub(match.group(), f"конец {match.group(1)}", first_bound, 1)

                if (match := re.match(rf"{MONTH_START_LAST_DAY} ({base_month_pattern})", second_bound)) and "начало" in raw:
                    second_bound = re.sub(match.group(), f"начало {match.group(1)}", second_bound, 1)
                elif (match := re.match(rf"{MONTH_MIDDLE_LAST_DAY} ({base_month_pattern})", second_bound)) and "середина" in raw:
                    second_bound = re.sub(match.group(), f"середина {match.group(1)}", second_bound, 1)
                elif match := re.match(rf"(\d+) ({base_month_pattern})", second_bound):
                    day, month = match.groups()

                    if int(day) == Date.last_day_in_month(year, month).day:
                        month_number = Date._encode_month(month)
                        nominative_month_label = RUSSIAN_FULL_MONTH_LABELS[month_number - 1]
                        second_bound = re.sub(match.group(), nominative_month_label, second_bound, 1)
                
                formatted_year = f"{first_bound} — {second_bound}"

        formatted_years.append(formatted_year)

    return "; ".join(formatted_years)


# def _date_sequence_to_editor_format(dates: list[Date | DateRange]) -> str:
#     # print(dates)

#     if any(
#         range.start_date.year != range.end_date.year 
#         for range in dates if isinstance(range, DateRange)
#     ):
#         raise NotImplementedError("Date sequence formatting is not implemented for the cases with ranges across different years.")

#     def retrieve_year(date: list[Date | DateRange]) -> int:
#         match date:
#             case Date(year=year):
#                 return year
#             case DateRange(start_date=start_bound, end_date=end_bound) if start_bound.year == end_bound.year:
#                 return start_bound.year
#             case _:
#                 raise NotImplementedError("Date sequence formatting is not implemented for the cases with ranges across different years.")
            
#     def retrieve_month(date: list[Date | DateRange]) -> int | tuple[int, int]:
#         match date:
#             case Date(month=month):
#                 return month
#             case DateRange(start_date=start_bound, end_date=end_bound) if start_bound.month == end_bound.month:
#                 return start_bound.month
#             case DateRange(start_date=start_bound, end_date=end_bound):
#                 return start_bound.month, end_bound.month
#             case _:
#                 raise NotImplementedError

#     dates_sorted_by_year = sorted(dates, key=retrieve_year)
#     dates_by_year = groupby(dates_sorted_by_year, key=retrieve_year)

#     formatted_years = []

#     for year, year_dates in dates_by_year:
#         year_dates = list(year_dates)
#         # try:
#         #     year_dates_sorted_by_month = sorted(year_dates, key=retrieve_month)
#         # except Exception as error:
#         #     pprint(year_dates)
#         #     raise error
#         year_dates_by_month = groupby(year_dates, key=retrieve_month)

#         formatted_months = []

#         for month, month_dates in year_dates_by_month:
#             month_dates = list(month_dates)

#             if type(month) is int:
#                 formatted_days = []

#                 for date in list(month_dates):
#                     match date:
#                         case Date(day=day) if day:
#                             formatted_days.append(f"{day}")
#                         case DateRange(start_date, end_date):
#                             start_day = f"{start_date.day}?" if start_date.is_uncertain else f"{start_date.day}"
#                             end_day = f"{end_date.day}?" if end_date.is_uncertain else f"{end_date.day}"
#                             formatted_days.append(f"{start_day}–{end_day}")
#                         case _:
#                             raise NotImplementedError
                
#                 formatted_month = ", ".join(formatted_days) + " " + get_genitive_month(month)
#                 formatted_months.append(formatted_month)
#             elif type(month) is tuple and len(list(month_dates)) == 1:
#                 month_date = list(month_dates)[0]
#                 start_day = f"{month_date.start_date.day}?" if month_date.start_date.is_uncertain else f"{month_date.start_date.day}"
#                 start_month = get_genitive_month(month_date.start_date.month)
#                 end_day = f"{month_date.end_date.day}?" if month_date.end_date.is_uncertain else f"{month_date.end_date.day}"
#                 end_month = get_genitive_month(month_date.end_date.month)
#                 formatted_months.append(f"{start_day} {start_month} – {end_day} {end_month}")
#             else:
#                 raise NotImplementedError
        
#         joined_formatted_months = ", ".join(formatted_months)
#         joined_formatted_months = delete_all_occurrences_except_last(
#             joined_formatted_months,
#             [f" {m}" for m in RUSSIAN_FULL_MONTH_LABELS_IN_GENETIVE_CASE],
#         )

#         formatted_year = f"{joined_formatted_months} {year} года"
#         formatted_years.append(formatted_year)
    
#     return "; ".join(formatted_years)


def date_union_to_editor_format(date_1: DateRange | Date, date_2: DateRange | Date) -> str:
    def retrieve_year(date: list[Date | DateRange]) -> int:
        match date:
            case Date(year=year):
                return year
            case DateRange(start_date=start_bound, end_date=end_bound) if start_bound.year == end_bound.year:
                return start_bound.year
            case _:
                raise NotImplementedError("Date sequence formatting is not implemented for the cases with ranges across different years.")
            
    def retrieve_month(date: list[Date | DateRange]) -> int:
        match date:
            case Date(month=month):
                return month
            case DateRange(start_date=start_bound, end_date=end_bound) if start_bound.month == end_bound.month:
                return start_bound.month
            case _:
                raise NotImplementedError("Date sequence formatting is not implemented for the cases with ranges across different months.")
    
    dates = [date_1, date_2]

    dates_by_year = groupby(dates, key=retrieve_year)
    assert len([year for year, _ in dates_by_year]) == 1

    dates_by_month = groupby(dates, key=retrieve_month)
    assert len([month for month, _ in dates_by_month]) == 1

    common_month = retrieve_month(date_1)
    common_year = retrieve_year(date_1)

    formatted_days = []

    for date in dates:
        match date:
            case Date(day=day) if day:
                formatted_days.append(f"{day}")
            case DateRange(start_date, end_date):
                start_day = f"{start_date.day}?" if start_date.is_uncertain else f"{start_date.day}"
                end_day = f"{end_date.day}?" if end_date.is_uncertain else f"{end_date.day}"
                formatted_days.append(f"{start_day}-{end_day}")
            case _:
                raise NotImplementedError
    
    return " или ".join(formatted_days) + f" {get_genitive_month(common_month)} {common_year} года"


@dataclass
class Symbol:
    AND = ","
    RANGE = "-"
    YEAR = "Y"
    HOUR = "H"
    MINUTE = "m"
    DAY = "D"
    MONTH = "M"
    UNCERTAIN = "Q"
    SILENT_UNCERTAIN = ""
    BEFORE = "<"
    AFTER = ">"
    AROUND = "~"
    OR = "|"
    PART = "%"
    SEASON = "S"
    FIRST_HALF = "^"
    LAST_HALF = "$"

    @cached_property
    @classmethod
    def values(cls):
        return [getattr(cls, field.name) for field in fields(cls)]


class DateEncoder:
    def __init__(self, year_label: str, month_label: str):
        self.year_label = year_label
        self.month_label = month_label

    def encode_year(self):
        return self._encode(self.year_label)

    def encode_month(self):
        return self._encode(self.month_label)

    def _encode(self, value):
        value = value.lower()

        value = re.sub("аперля", "апреля", value)
        value = re.sub("i", "1", value)
        value = re.sub("мая б", "мая 6", value)

        value = re.sub(r",", ", ", value)
        value = re.sub(r"\(", " ( ", value)
        value = re.sub(r"\)", " ) ", value)
        value = re.sub(r"г\.", "", value, flags=re.I)
        value = re.sub(r"^(.*?)$", r" \1 ", value)
        value = re.sub(r"\s+", " ", value)

        value = re.sub(r"[-—]+", Symbol.RANGE, value)
        value = re.sub(rf"{base_month_pattern}", Symbol.MONTH, value, flags=re.I)
        value = re.sub(r"\d{4}", Symbol.YEAR, value)
        value = re.sub(r"\d+\s*ч\.?", Symbol.HOUR, value)
        value = re.sub(r"\d+\s*м\.?", Symbol.MINUTE, value)
        value = re.sub(r"\d+", Symbol.DAY, value)
        value = re.sub(r"\( \? \)|\?", Symbol.SILENT_UNCERTAIN, value)
        value = re.sub(r"\s+(после|с|не ранее)\s+", Symbol.AFTER, value, flags=re.I)
        value = re.sub(r"\s+(до|перед|не позднее|ранее)\s+", Symbol.BEFORE, value, flags=re.I)
        value = re.sub(r"\s+около\s+", Symbol.AROUND, value, flags=re.I)
        value = re.sub(r"\s+(или)\s+", Symbol.OR, value, flags=re.I)
        value = re.sub(r"\s+(и)\s+", Symbol.AND, value, flags=re.I)
        value = re.sub(r"(на[чп]ало|середина|конец)", Symbol.PART, value, flags=re.I)
        value = re.sub(r"\s+(зима|весна|лето|осень)\s+", Symbol.SEASON, value, flags=re.I)
        
        value = re.sub(r"\s+", "", value)
        value = re.sub(r"M,", "M", value)

        value = re.sub(r"перваяполовина", Symbol.FIRST_HALF, value, flags=re.I)
        value = re.sub(r"втораяполовина", Symbol.LAST_HALF, value, flags=re.I)

        value = value.strip(" ,.-")
        value = re.sub(r"\s+и$", "", value)
        value = value.strip(" ,.-")

        value = re.sub(r"первыечисла|последниечисла", Symbol.PART, value, flags=re.I)
        value = re.sub(r"M\.", "M", value)

        return value

month_range_part_pattern = "|".join(sorted("M|MD(,D)*|M%|M<D|M>D|M%,<D|M~D|M%,>D".split("|"), key=lambda x: -len(x)))
month_range_pattern = rf"({month_range_part_pattern})-({month_range_part_pattern})"

month_with_day_or_day_range_sequence_pattern = "M(D|D-D)(,?(D|D-D))*"

question_mark_pattern = r"\(\?\)|\?"
year_pattern = rf"(\d\d\d\d)\s*({question_mark_pattern})?"
year_range_pattern = rf"({year_pattern})\s*-\s*({year_pattern})"


def normalize_whitespace(string: str) -> str:
    return re.sub("\s+", " ", string.strip())


@dataclass
class DateTagsConfig:
    dates: list[Date | DateRange]
    editor_date_label: str
    date_pattern: str
    raw_date: str


class DateProcessor:
    def __init__(self, year_label: str, month_label: str):
        self.year_label = year_label
        self.month_label = month_label

    def can_be_processed(self):
        return bool(self.parse())

    def parse(self) -> DateTagsConfig | None:
        # Convert month to code
        encoder = DateEncoder(self.year_label, self.month_label)
        code = encoder.encode_month()
        year_code = encoder.encode_year()

        date_pattern = f'[{year_code}] "{code}"'
        raw_date = f'[{normalize_whitespace(self.year_label)}] "{normalize_whitespace(self.month_label)}"'

        # Process dates where parentheses don't mean gregorian mode
        match code:
            case "октябрей(MD)":
                return DateTagsConfig(
                    dates=[Date(year=1867, month=10, day=28)],
                    editor_date_label="28 октября (9 ноября) 1867 года",
                    date_pattern=date_pattern,
                    raw_date=raw_date,
                )
            case "лето,<отъездавмоскву(DM)":
                return DateTagsConfig(
                    dates=[DateRange(
                        start_date=Date(year=1882, month=6, day=1),
                        end_date=Date(year=1882, month=9, day=10),
                    )],
                    editor_date_label="лето 1882 года, до отъезда в Москву (10 сентября)",
                    date_pattern=date_pattern,
                    raw_date=raw_date,
                )
            case "M-M(D)":
                range = DateRange(
                    start_date=Date(year=1893, month=5, day=1),
                    end_date=Date(year=1893, month=8, day=2),
                )

                range.is_uncertain = True

                return DateTagsConfig(
                    dates=[range],
                    editor_date_label="май – август (2) 1893 года",
                    date_pattern=date_pattern,
                    raw_date=raw_date,
                )
            case "M%-M(<D)Y":
                # [1882] "Декабрь, конец — январь (не позднее 15) 1883 г."

                return DateTagsConfig(
                    dates=[DateRange(
                        start_date=Date(year=1882, month=12, day=MONTH_END_FIRST_DAY),
                        end_date=Date(year=1883, month=1, day=15, is_uncertain=True),
                    )],
                    editor_date_label="лето 1882 года, до отъезда в Москву (10 сентября)",
                    date_pattern=date_pattern,
                    raw_date=raw_date,
                )
            case "D(MD)":
                # [1870] "29 (июня 9)"
                
                return DateTagsConfig(
                    dates=[Date(year=1867, month=10, day=28)],
                    editor_date_label="28 октября (9 ноября) 1867 года",
                    date_pattern=date_pattern,
                    raw_date=raw_date,
                )

        # List informative code tails
        misc_code_endings = [
            ",Hmдня,Hmдня,Hmвечера",
            ",Hmвечера",
            ",Hmдня",
            ",Hmутра",
            ",вечер",
            ",Hутра",
            ",междуD-Hас.утра",
            ",междуD,Hдня",
            ",междуD,Hас.вечера",
            ",утро",
            ",ночь",
            ",Hдня",
            ",Hвечера",
            ",~Hутра",
            ",~Hас.утра",
            ",Hасовутра",
            ",Hасдня",
            ",Hас.утра",
            ",пасха",
            ",ночью",
            ",часночи",
            ",часдня",
            ",отHm<Hmдня",
            ",отHm<Hmдня",
            ",междуD-Hас.утра",
            ",междуD,Hдня",
            ",междуD,Hас.вечера",
            ",восемьчасовутра",
            ",~Hвечера",
            ",~Hасутра",
            ",~Hасовутра",
            ",Hасаночи",
            ",Hасоввечера"
            ",mинутпервогоночи",
            ",Hасовночи",
            ",>обеда",
            ",>Hвечера",
            ",<Hmутра",
            ",Hас.дня",
            ",D-й,часутра",
            ",Hас.ночи",
            ",D½час.ночи",
            ",D-йчасутра",
            ",Hm",
            ",Hmночи",
            ",ночьнаD",
            "Hас.вечера",
            "Hвечера",
            "Hасадня",
            "Hас.утра",
            "Hас.mутра",
            "Hmвечера",
            "Hmутра",
            "(п.ш.тула)",
            "(масленица)",
            "(первыйденьпасхи)",
            "(«прощеноевоскресенье»)",
            "(«краснаягорка»)",
        ]

        separated_tail = ""

        # Separate unparsable tails from the code and the raw month label
        for ending in sorted(misc_code_endings, key=lambda x: -len(x)):
            if re.search(rf"{re.escape(ending)}$", code):

                # Separate exceptions
                if ending in [",междуD,Hас.вечера", ",междуD,Hдня"]:
                    start, end = self.month_label.split(",")
                    self.month_label = start
                    separated_tail = f", {end}"
                    break

                # Separate tails starting with a comma
                if ending.startswith(","):
                    ending_comma_count = ending.count(",")
                    *start, end = self.month_label.split(",", len(self.month_label.split(",")) - ending_comma_count)
                    separated_tail = f", {end.strip()}"
                    self.month_label = ", ".join(start)
                    break

                # Separate tails wrapped in parentheses
                if re.match(r"\(.*?\)", ending, re.DOTALL):
                    match = re.match(r"(.*?)(\(.*?\))$", self.month_label, re.DOTALL)
                    start, end = match.groups()
                    separated_tail = f" {end.strip()}"
                    self.month_label = start
                    break

                # Separate unique tails
                match ending:
                    case "Hас.вечера":
                        match = re.match(r"(.*?)(\d+\s*час\.\s*вечера)$", self.month_label, re.DOTALL)
                        start, end = match.groups()
                        separated_tail = f" {end.strip()}"
                        self.month_label = start
                        break
                    case "Hвечера":
                        match = re.match(r"(.*?)(\d+\s*ч\.?\s*вечера)$", self.month_label, re.DOTALL)
                        start, end = match.groups()
                        separated_tail = f" {end.strip()}"
                        self.month_label = start
                        break
                    case "Hасадня":
                        match = re.match(r"(.*?)(\d+\s*часа\s*дня)$", self.month_label, re.DOTALL)
                        start, end = match.groups()
                        separated_tail = f" {end.strip()}"
                        self.month_label = start
                        break
                    case "Hас.утра":
                        match = re.match(r"(.*?)(\d+\s*час\.\s*утра)$", self.month_label, re.DOTALL)
                        start, end = match.groups()
                        separated_tail = f" {end.strip()}"
                        self.month_label = start
                        break
                    case "Hас.mутра":
                        try:
                            match = re.match(r"(.*?)(\d+\s*час\.\s*\d+\s*м\.?\s*утра)$", self.month_label, re.DOTALL)
                            start, end = match.groups()
                            separated_tail = f" {end.strip()}"
                            self.month_label = start
                            break
                        except Exception as error:
                            print(self.month_label)
                            raise error
                    case "Hmвечера":
                        match = re.match(r"(.*?)(\d+\s*ч\.?\s*\d+\s*м\.?\s*вечера)$", self.month_label, re.DOTALL)
                        start, end = match.groups()
                        separated_tail = f" {end.strip()}"
                        self.month_label = start
                        break
                    case "Hmутра":
                        match = re.match(r"(.*?)(\d+\s*ч\.?\s*\d+\s*м\.?\s*утра)$", self.month_label, re.DOTALL)
                        start, end = match.groups()
                        separated_tail = f" {end.strip()}"
                        self.month_label = start
                        break

        # Remove the separated tail from the month code
        code = re.sub(
            r"|".join([rf"{re.escape(v)}$" for v in sorted(misc_code_endings, key=lambda x: -len(x))]),
            "",
            code,
            flags=re.DOTALL
        )

        # Remove parenthesized gregorian equivalents from code
        code = re.sub(r"\(.*?\)", "", code, flags=re.DOTALL).strip(" ,;-")

        # Remove parenthesized gregorian equivalents from raw month label
        self.month_label = re.sub(
            r"\((.*?)\)\s*(\(\?\))?",
            lambda m: m.group(0) if m.group(1) == "?" else "",
            self.month_label,
            flags=re.DOTALL,
        )

        try:
            if re.match("^Y$", year_code):
                year_match = re.match(rf"^({year_pattern})$", self.year_label.strip())
                year_string, q = year_match.group(2), year_match.group(3)
                year_date = Date(year_string, is_uncertain=has_value(q))
                year = str(year_date.year)

                if re.match(r"^M(D|D-D)(,?(D|D-D))*$", code):
                    dates = convert_single_month_day_or_range_sequence(self.month_label, year)
                    editor_date_label = date_sequence_to_editor_format(dates)
                    
                    return DateTagsConfig(
                        dates=dates,
                        editor_date_label=editor_date_label + separated_tail,
                        date_pattern=date_pattern,
                        raw_date=raw_date,
                    )
                
                if re.match(r"^M$", code):
                    date = convert_single_month(self.month_label, year)
                    editor_date_label = date.to_editor_format()
                    
                    return DateTagsConfig(
                        dates=[date],
                        editor_date_label=editor_date_label + separated_tail,
                        date_pattern=date_pattern,
                        raw_date=raw_date,
                    )
                
                if re.match(r"^M%(-%)?$", code):
                    date = convert_month_part_or_range(self.month_label, year)
                    editor_date_label = date.to_editor_format()

                    return DateTagsConfig(
                        dates=[date],
                        editor_date_label=editor_date_label + separated_tail,
                        date_pattern=date_pattern,
                        raw_date=raw_date,
                    )
                
                if re.match(r"^M~D$", code):
                    date = convert_around_month_day(self.month_label, year)
                    editor_date_label = date.to_editor_format()
                    
                    return DateTagsConfig(
                        dates=[date],
                        editor_date_label=editor_date_label + separated_tail,
                        date_pattern=date_pattern,
                        raw_date=raw_date,
                    )
                
                if re.match(r"^M>D$", code):
                    date = convert_after_month_day(self.month_label, year)
                    editor_date_label = date.to_editor_format()

                    return DateTagsConfig(
                        dates=[date],
                        editor_date_label=editor_date_label + separated_tail,
                        date_pattern=date_pattern,
                        raw_date=raw_date,
                    )
                
                if re.match(r"^M<D$", code):
                    date = convert_before_month_day(self.month_label, year)
                    editor_date_label = date.to_editor_format()
                    
                    return DateTagsConfig(
                        dates=[date],
                        editor_date_label=editor_date_label + separated_tail,
                        date_pattern=date_pattern,
                        raw_date=raw_date,
                    )
                
                if re.match(r"^MD\|D$", code):
                    dates = convert_or_day_in_month(self.month_label, year)
                    editor_date_label = date_union_to_editor_format(*dates)
                    
                    return DateTagsConfig(
                        dates=dates,
                        editor_date_label=editor_date_label + separated_tail,
                        date_pattern=date_pattern,
                        raw_date=raw_date, 
                    )
                
                if re.match(r"^MD-D\|D$", code):
                    dates = convert_or_day_range_in_month(self.month_label, year)
                    editor_date_label = date_union_to_editor_format(*dates)
                    
                    return DateTagsConfig(
                        dates=dates,
                        editor_date_label=editor_date_label + separated_tail,
                        date_pattern=date_pattern,
                        raw_date=raw_date,
                    )
                
                if re.match(r"^M%(-%)?,>D$", code):
                    date = convert_month_part_after_day(self.month_label, year)
                    editor_date_label = date.to_editor_format()

                    return DateTagsConfig(
                        dates=[date],
                        editor_date_label=editor_date_label + separated_tail,
                        date_pattern=date_pattern,
                        raw_date=raw_date, 
                    )
                
                if re.match(r"^M%(-%)?,<D$", code):
                    date = convert_month_part_before_day(self.month_label, year)
                    editor_date_label = date.to_editor_format()

                    return DateTagsConfig(
                        dates=[date],
                        editor_date_label=editor_date_label + separated_tail,
                        date_pattern=date_pattern,
                        raw_date=raw_date,
                    )
                
                if re.match(r"^M\^$", code):
                    date = convert_month_first_half(self.month_label, year)
                    editor_date_label = date.to_editor_format()

                    return DateTagsConfig(
                        dates=[date],
                        editor_date_label=editor_date_label + separated_tail,
                        date_pattern=date_pattern,
                        raw_date=raw_date,
                    )
                
                if re.match(r"^M\$$", code):
                    date = convert_month_second_half(self.month_label, year)
                    editor_date_label = date.to_editor_format()

                    return DateTagsConfig(
                        dates=[date],
                        editor_date_label=editor_date_label + separated_tail,
                        date_pattern=date_pattern,
                        raw_date=raw_date,
                    )
                
                if re.match(r"^Mночь,?>DнаD(-е)?", code):
                    date = convert_month_night(self.month_label, year)
                    editor_date_label = date.to_editor_format()

                    return DateTagsConfig(
                        dates=[date],
                        editor_date_label=editor_date_label + separated_tail,
                        date_pattern=date_pattern,
                        raw_date=raw_date,
                    )
                
                if re.match(r"^MмеждуD[,-]D", code):
                    date = convert_month_between_days(self.month_label, year)
                    editor_date_label = date.to_editor_format()

                    return DateTagsConfig(
                        dates=[date],
                        editor_date_label=editor_date_label + separated_tail,
                        date_pattern=date_pattern,
                        raw_date=raw_date,
                    )
                
                if re.match(rf"^{month_range_pattern}$", code):
                    date_or_dates = convert_month_range(self.month_label, year, code)
                    dates = date_or_dates if type(date_or_dates) is list else [date_or_dates]
                    editor_date_label = date_sequence_to_editor_format(dates, self.month_label, convert_ranges=True)
                    
                    return DateTagsConfig(
                        dates=dates,
                        editor_date_label=editor_date_label + separated_tail,
                        date_pattern=date_pattern,
                        raw_date=raw_date,
                    )
                
                if re.match(rf"^({month_with_day_or_day_range_sequence_pattern})([,;]({month_with_day_or_day_range_sequence_pattern}))+$", code):
                    dates = convert_sequence_of_months(self.month_label, year)
                    editor_date_label = date_sequence_to_editor_format(dates, self.month_label)
                    
                    return DateTagsConfig(
                        dates=dates,
                        editor_date_label=editor_date_label + separated_tail,
                        date_pattern=date_pattern,
                        raw_date=raw_date,
                    )
                
                if re.match(rf"^Y$", code):
                    date = convert_year_date(self.month_label, year)
                    editor_date_label = date.to_editor_format()
                    
                    return DateTagsConfig(
                        dates=[date],
                        editor_date_label=editor_date_label + separated_tail,
                        date_pattern=date_pattern,
                        raw_date=raw_date,
                    )
                
                if re.match(rf"^{question_mark_pattern}$", preprocess(self.month_label)):
                    date = convert_year_date(year, year)
                    date.is_uncertain = True
                    editor_date_label = date.to_editor_format()
                    
                    return DateTagsConfig(
                        dates=[date],
                        editor_date_label=editor_date_label + separated_tail,
                        date_pattern=date_pattern,
                        raw_date=raw_date,
                    )
                
                if code == "":
                    date = convert_year_date(year, year)
                    editor_date_label = date.to_editor_format()
                    
                    return DateTagsConfig(
                        dates=[date],
                        editor_date_label=editor_date_label + separated_tail,
                        date_pattern=date_pattern,
                        raw_date=raw_date,
                    )
                
                if re.match(rf"^Y-Y$", code):
                    date = convert_year_range(self.month_label)
                    editor_date_label = date.to_editor_format()
                    
                    return DateTagsConfig(
                        dates=[date],
                        editor_date_label=editor_date_label + separated_tail,
                        date_pattern=date_pattern,
                        raw_date=raw_date,
                    )
                
                if re.match(rf"^S$", code):
                    date = convert_season(self.month_label, year)
                    editor_date_label = date.to_editor_format()
                    
                    return DateTagsConfig(
                        dates=[date],
                        editor_date_label=editor_date_label + separated_tail,
                        date_pattern=date_pattern,
                        raw_date=raw_date,
                    )
            
            if re.match(rf"^Y-Y$", year_code):
                if code == "" or re.match(r"^(Y|Y-Y)$", code):
                    date = convert_year_range(self.year_label)
                    editor_date_label = date.to_editor_format()
                    
                    return DateTagsConfig(
                        dates=[date],
                        editor_date_label=editor_date_label + separated_tail,
                        date_pattern=date_pattern,
                        raw_date=raw_date,
                    )
        
        except Exception as error:
            print(code)
            print(f'"{self.year_label, self.month_label}"')
            print(f'"{preprocess(self.month_label)}"')
            raise error
        
        # TODO: parse remaining failing dates
        return DateTagsConfig(
            dates=[],
            editor_date_label="",
            date_pattern=date_pattern,
            raw_date=raw_date,
        )
    

def convert_month_part_to_date_range(month_part: MonthPartLabel, month, year) -> DateRange:
    match month_part:
        case MonthPartLabel.START:
            start_date = Date.first_day_in_month(year, month)
            end_date = Date(year, month, MONTH_START_LAST_DAY)
            return DateRange(start_date, end_date)
        
        case MonthPartLabel.MIDDLE:
            start_date = Date(year, month, MONTH_MIDDLE_FIRST_DAY)
            end_date = Date(year, month, MONTH_MIDDLE_LAST_DAY)
            return DateRange(start_date, end_date)
        
        case MonthPartLabel.END:
            start_date = Date(year, month, MONTH_END_FIRST_DAY)
            end_date = Date.last_day_in_month(year, month)
            return DateRange(start_date, end_date)
    
    raise NotImplementedError(f"Failed to convert {month_part} to date range.")


def preprocess(raw: str):
    value = raw.lower().strip(' \n,-')
    value = re.sub("аперля", "апреля", value)
    value = re.sub("i", "1", value)
    value = re.sub("мая б", "мая 6", value)
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"[-—]+", "-", value)
    value = re.sub(r"(\d+)\s+(\d+)", r"\1, \2", value)
    value = re.sub(r"(\d)\s*и\s*(\d)", r"\1, \2", value)
    value = re.sub(rf"(,\s+)({question_mark_pattern})\s+({day_or_range_pattern})", r"\1\3 (?)", value)
    value = re.sub("первые числа", "начало", value)
    value = re.sub("последние числа", "конец", value)
    value = value.strip(" ,;.-")
    return value



day_pattern = rf"(\d+)\s*({question_mark_pattern})?"
day_range_pattern = rf"({day_pattern})\s*-\s*({day_pattern})"
day_or_range_pattern = rf"{day_range_pattern}|{day_pattern}"
day_or_range_sequence_pattern = rf"({day_or_range_pattern})(\s*[,и]?\s*({day_or_range_pattern}))*"
month_plus_day_or_range_sequence_pattern = rf"^({base_month_pattern})\s*,?\s*({day_or_range_sequence_pattern})$"

month_pattern = rf"({base_month_pattern})\s*({question_mark_pattern})?"

part_pattern = rf"(на[чп]ало|середина|конец)\s*({question_mark_pattern})?"
part_range_pattern = rf"({part_pattern})\s*-\s*({part_pattern})"
part_or_range_pattern = rf"({part_range_pattern})|({part_pattern})"

around_day_pattern = rf"около ({day_pattern})"

after_pattern = "после|с|не ранее"
after_day_pattern = rf"({after_pattern}) ({day_pattern})"

before_pattern = "до|перед|не позднее|ранее"
before_day_pattern = rf"({before_pattern}) ({day_pattern})"

or_day_pattern = rf"({day_pattern})\s*или\s*({day_pattern})"
or_day_range_pattern = rf"({day_range_pattern})\s*или\s*({day_pattern})"

part_or_range_after_day_pattern = rf"({part_or_range_pattern})\s*,?\s*({after_day_pattern})"
part_or_range_before_day_pattern = rf"({part_or_range_pattern})\s*,?\s*({before_day_pattern}|(-)\s*(\d+))"

month_first_half_pattern = rf"({base_month_pattern})\s*,?\s*первая\s*половина"
month_second_half_pattern = rf"({base_month_pattern})\s*,?\s*вторая\s*половина"

night_pattern = rf"ночь\s*,?\s+((с\s+)?\d+\s+)на\s+(\d+)(-е)?"

between_days_pattern = rf"между\s*({day_pattern})\s*[и,-]\s*({day_pattern})"

season_pattern = r"зима|весна|лето|осень"

"M-M"

"M|MD(,D)?|M%|M<D|M>D|MDY|MY|M%,<D|M~D|Y,M"



def has_value(string: str | None):
    return bool(string and string.strip())


# PATTERN TO DATE


def convert_day_pattern_to_date(day, month, year) -> Date:
    day, q = re.match(day_pattern, day).groups()
    return Date(year, month, day, is_uncertain=has_value(q))


def convert_day_range_pattern_to_date_range(range, month, year) -> DateRange:
    start_day, _, __, end_day, ___, ____ = re.match(day_range_pattern, range).groups()
    start_date = convert_day_pattern_to_date(start_day, month, year)
    end_date = convert_day_pattern_to_date(end_day, month, year)
    return DateRange(start_date, end_date)


def convert_day_or_range_pattern_to_date(pattern, month, year) -> DateRange | Date:
    if re.match(day_range_pattern, pattern):
        return convert_day_range_pattern_to_date_range(pattern, month, year)
    
    if re.match(day_pattern, pattern):
        return convert_day_pattern_to_date(pattern, month, year)

    raise ValueError(f"Unexpected pattern {pattern}")


def convert_day_or_range_sequence_pattern_to_dates(pattern, month, year) -> list[DateRange | Date]:
    days_or_ranges = re.split("\s*,\s*", pattern)

    dates = []

    for day_or_range in days_or_ranges:
        dates.append(convert_day_or_range_pattern_to_date(day_or_range, month, year))

    return dates


def convert_month_pattern_to_date(pattern, year) -> DateRange:
    match = re.match(month_pattern, pattern)
    month, q = match.groups()

    range = DateRange.month(year, month)
    range.is_uncertain = has_value(q)
    return range


def convert_part_pattern_to_date(pattern, month, year) -> DateRange:
    match = re.match(part_pattern, pattern)
    part, q = match.groups()
    is_uncertain = has_value(q)

    match part:
        case "начало" | "напало":
            return DateRange.start_of_month(year, month, is_uncertain)
        case "середина":
            return DateRange.middle_of_month(year, month, is_uncertain)
        case "конец":
            return DateRange.end_of_month(year, month, is_uncertain)
        case _:
            raise ValueError(f"Unexpected part label: {pattern}")
        

def convert_part_range_pattern_to_date(pattern, month, year) -> DateRange:
    match = re.match(part_range_pattern, pattern)
    first_part, second_part = match.group(1), match.group(4)
    first_date = convert_part_pattern_to_date(first_part, month, year)
    second_date = convert_part_pattern_to_date(second_part, month, year)
    return DateRange(first_date.start_date, second_date.end_date, part_range=(first_date.part, second_date.part))


def convert_part_or_range_pattern_to_date(pattern, month, year) -> DateRange:
    if re.match(part_range_pattern, pattern):
        return convert_part_range_pattern_to_date(pattern, month, year)
    
    if re.match(part_pattern, pattern):
        return convert_part_pattern_to_date(pattern, month, year)
    
    raise ValueError(f"Unexpected: {pattern}")


def convert_around_day_pattern_to_date(pattern, month, year) -> Date:
    match = re.match(around_day_pattern, pattern)
    day = match.group(1)
    date = convert_day_pattern_to_date(day, month, year)
    date.is_around = True
    return date


def convert_after_day_pattern_to_date(pattern, month, year) -> DateRange:
    # TODO: согласовать необходимость разделения по точности
    match = re.match(after_day_pattern, pattern)
    label, day = match.group(1), match.group(2)
    start_date = convert_day_pattern_to_date(day, month, year)
    end_date = Date.last_day_in_month(year, month)
    range = DateRange(start_date, end_date)
    range.after_label = label
    return range


def convert_before_day_pattern_to_date(pattern, month, year) -> DateRange:
    # TODO: согласовать необходимость разделения по точности
    match = re.match(before_day_pattern, pattern)
    label, day = match.group(1), match.group(2)
    start_date = Date.first_day_in_month(year, month)
    end_date = convert_day_pattern_to_date(day, month, year)
    range = DateRange(start_date, end_date)
    range.before_label = label
    return range


def convert_or_day_pattern_to_date(pattern, month, year) -> tuple[Date, Date]:
    match = re.match(or_day_pattern, pattern)
    first_day, _, _, second_day, *_ = match.groups()
    first_date = convert_day_pattern_to_date(first_day, month, year)
    second_date = convert_day_pattern_to_date(second_day, month, year)

    first_date.is_uncertain = True
    second_date.is_uncertain = True
    return [first_date, second_date]


def convert_or_day_range_pattern_to_date(pattern, month, year) -> tuple[DateRange, Date]:
    match = re.match(or_day_range_pattern, pattern)
    first_range, second_day = match.group(1), match.group(8)
    first_date = convert_day_range_pattern_to_date_range(first_range, month, year)
    second_date = convert_day_pattern_to_date(second_day, month, year)

    first_date.is_uncertain = True
    second_date.is_uncertain = True
    return [first_date, second_date]


def convert_or_day_range_pattern_to_date(pattern, month, year) -> tuple[DateRange, Date]:
    match = re.match(or_day_range_pattern, pattern)
    first_range, second_day = match.group(1), match.group(8)
    first_date = convert_day_range_pattern_to_date_range(first_range, month, year)
    second_date = convert_day_pattern_to_date(second_day, month, year)

    first_date.is_uncertain = True
    second_date.is_uncertain = True
    return [first_date, second_date]


def convert_part_after_day_pattern_to_date(pattern, month, year) -> DateRange:
    match = re.match(part_or_range_after_day_pattern, pattern)
    part_or_range, after_day = match.group(1), match.group(12)
    range_date = convert_part_or_range_pattern_to_date(part_or_range, month, year)
    after_date_range = convert_after_day_pattern_to_date(after_day, month, year)
    
    output_range = DateRange(
        after_date_range.start_date, 
        range_date.end_date, 
        after_label=after_date_range.after_label,
    )

    if range_date.part:
        output_range.part = range_date.part
    elif range_date.part_range:
        output_range.part_range = range_date.part_range

    return output_range


def convert_part_before_day_pattern_to_date(pattern, month, year) -> DateRange:
    match = re.match(part_or_range_before_day_pattern, pattern)
    part_or_range, before_day = match.group(1), match.group(12)
    range_date = convert_part_or_range_pattern_to_date(part_or_range, month, year)
    before_date_range = convert_before_day_pattern_to_date(before_day, month, year)

    output_range = DateRange(
        range_date.start_date, 
        before_date_range.end_date,
        before_label=before_date_range.before_label
    )

    if range_date.part:
        output_range.part = range_date.part
    elif range_date.part_range:
        output_range.part_range = range_date.part_range

    return output_range


def convert_month_first_half_to_date(pattern, year) -> DateRange:
    match = re.match(month_first_half_pattern, pattern)
    month = match.group(1)
    return DateRange.first_half_of_month(year, month)


def convert_month_second_half_to_date(pattern, year) -> DateRange:
    match = re.match(month_second_half_pattern, pattern)
    month = match.group(1)
    return DateRange.last_half_of_month(year, month)


def convert_night_pattern_to_date(pattern, month, year) -> DateRange:
    match = re.match(night_pattern, pattern)
    second_day = match.group(3)
    first_date = Date(year, month, int(second_day) - 1)
    second_date = Date(year, month, second_day)
    range = DateRange(first_date, second_date)
    range.is_night = True
    return range


def convert_between_days_pattern(pattern, month, year) -> DateRange:
    match = re.match(between_days_pattern, pattern)
    first_day, second_day = match.group(1), match.group(4)
    first_date = convert_day_pattern_to_date(first_day, month, year)
    second_date = convert_day_pattern_to_date(second_day, month, year)
    return DateRange(first_date, second_date)


# STRING TO DATE


"M|MD(,D)?|M%|M<D|M>D|MDY|MY|M%,<D|M~D|Y,M"

"""
M
convert_month_pattern_to_date

---

MD
convert_single_month_day_or_range_sequence
^(?P<month>{base_month_pattern})\s*[,.]?\s*(?P<sequence>{day_or_range_sequence_pattern})$

---

M%
convert_month_part_or_range
^(?P<month>{base_month_pattern})\s*[,.]?\s*(?P<part>{part_or_range_pattern})$

---

M>D
convert_after_month_day
^(?P<month>{base_month_pattern})\s*[,.]?\s*(?P<day>{after_day_pattern})$

---

M<D
convert_before_month_day
^(?P<month>{base_month_pattern})\s*[,.]?\s*(?P<day>{before_day_pattern})$

---

M%,<D
convert_month_part_before_day
^(?P<month>{base_month_pattern})\s*[,.]?\s*(?P<date>{part_or_range_before_day_pattern})$

---

M%,>D
convert_month_part_after_day
^(?P<month>{base_month_pattern})\s*[,.]?\s*(?P<date>{part_or_range_after_day_pattern})$

---

M~D
convert_around_month_day
^(?P<month>{base_month_pattern})\s*[,.]?\s*(?P<day>{around_day_pattern})$

"""


def convert_single_month_day(raw: str, year) -> Date:
    string = preprocess(raw)
    match = re.match(rf"^(?P<month>{base_month_pattern})\s*[,.]?\s*(?P<day>{day_pattern})$", string)
    month = match.group("month")
    day = match.group("day")
    return convert_day_pattern_to_date(day, month, year)


def convert_single_month_day_range(raw: str, year) -> DateRange:
    string = preprocess(raw)
    match = re.match(rf"^(?P<month>{base_month_pattern})\s*[,.]?\s*(?P<range>{day_range_pattern})$", string)
    month = match.group("month")
    range = match.group("range")
    return convert_day_range_pattern_to_date_range(range, month, year)


def convert_single_month_day_sequence(raw: str, year) -> DateRange:
    string = preprocess(raw)
    question_mark_pattern = r"\(\?\)|\?"
    day_pattern = rf"(\d+)\s*({question_mark_pattern})?"
    month, _, start_day, start_day_q, __, end_day, end_day_q = re.match(rf"^({base_month_pattern})\s*,?\s*({day_pattern})\s*-\s*({day_pattern})$", string).groups()

    start_date = Date(year, month, start_day, is_uncertain=bool(start_day_q and start_day_q.strip()))
    end_date = Date(year, month, end_day, is_uncertain=bool(end_day_q and end_day_q.strip()))
    
    return DateRange(start_date, end_date)


def convert_single_month_day_or_range_sequence(raw: str, year) -> list[DateRange | Date]:
    string = preprocess(raw)
    match = re.match(rf"^(?P<month>{base_month_pattern})\s*[,.]?\s*(?P<sequence>{day_or_range_sequence_pattern})$", string)
    month, sequence = match.group("month"), match.group("sequence")
    return convert_day_or_range_sequence_pattern_to_dates(sequence, month, year)


def convert_single_month(raw: str, year) -> DateRange:
    string = preprocess(raw)
    match = re.match(rf"^(?P<month>{month_pattern})(\s+и)?$", string)
    month = match.group("month")
    return convert_month_pattern_to_date(month, year)


def convert_month_part(raw: str, year) -> DateRange:
    string = preprocess(raw)
    match = re.match(rf"^(?P<month>{base_month_pattern})\s*[,.]?\s*(?P<part>{part_pattern})$", string)
    month, part = match.group("month"), match.group("part")
    return convert_part_pattern_to_date(part, month, year)


def convert_month_part_range(raw: str, year) -> DateRange:
    string = preprocess(raw)
    match = re.match(rf"^(?P<month>{base_month_pattern})\s*[,.]?\s*(?P<range>{part_range_pattern})$", string)
    month, range = match.group("month"), match.group("range")
    return convert_part_range_pattern_to_date(range, month, year)


def convert_month_part_or_range(raw: str, year) -> DateRange:
    string = preprocess(raw)
    match = re.match(rf"^(?P<month>{base_month_pattern})\s*[,.]?\s*(?P<part>{part_or_range_pattern})$", string)
    month, part = match.group("month"), match.group("part")
    return convert_part_or_range_pattern_to_date(part, month, year)


def convert_around_month_day(raw: str, year) -> DateRange:
    string = preprocess(raw)
    match = re.match(rf"^(?P<month>{base_month_pattern})\s*[,.]?\s*(?P<day>{around_day_pattern})$", string)
    month, day = match.group("month"), match.group("day")
    return convert_around_day_pattern_to_date(day, month, year)


def convert_after_month_day(raw: str, year):
    string = preprocess(raw)
    match = re.match(rf"^(?P<month>{base_month_pattern})\s*[,.]?\s*(?P<day>{after_day_pattern})$", string)
    month, day = match.group("month"), match.group("day")
    return convert_after_day_pattern_to_date(day, month, year)


def convert_before_month_day(raw: str, year):
    string = preprocess(raw)
    match = re.match(rf"^(?P<month>{base_month_pattern})\s*[,.]?\s*(?P<day>{before_day_pattern})$", string)
    month, day = match.group("month"), match.group("day")
    return convert_before_day_pattern_to_date(day, month, year)


def convert_or_day_in_month(raw: str, year) -> tuple[Date, Date]:
    string = preprocess(raw)
    match = re.match(rf"^(?P<month>{base_month_pattern})\s*[,.]?\s*(?P<days>{or_day_pattern})$", string)
    month, days = match.group("month"), match.group("days")
    return convert_or_day_pattern_to_date(days, month, year)


def convert_or_day_range_in_month(raw: str, year):
    string = preprocess(raw)
    match = re.match(rf"^(?P<month>{base_month_pattern})\s*[,.]?\s*(?P<days>{or_day_range_pattern})$", string)
    month, days = match.group("month"), match.group("days")
    return convert_or_day_range_pattern_to_date(days, month, year)


def convert_month_part_after_day(raw: str, year):
    string = preprocess(raw)
    match = re.match(rf"^(?P<month>{base_month_pattern})\s*[,.]?\s*(?P<date>{part_or_range_after_day_pattern})$", string)
    month, date = match.group("month"), match.group("date")
    return convert_part_after_day_pattern_to_date(date, month, year)


def convert_month_part_before_day(raw: str, year):
    string = preprocess(raw)
    match = re.match(rf"^(?P<month>{base_month_pattern})\s*[,.]?\s*(?P<date>{part_or_range_before_day_pattern})$", string)
    month, date = match.group("month"), match.group("date")
    return convert_part_before_day_pattern_to_date(date, month, year)


def convert_month_first_half(raw: str, year):
    string = preprocess(raw)
    return convert_month_first_half_to_date(string, year)


def convert_month_second_half(raw: str, year):
    string = preprocess(raw)
    return convert_month_second_half_to_date(string, year)


def convert_month_night(raw: str, year):
    string = preprocess(raw)
    match = re.match(rf"^(?P<month>{base_month_pattern})\s*[,.]?\s+(\d+)?,?\s*(?P<night>{night_pattern})", string)
    month, night = match.group("month"), match.group("night")
    return convert_night_pattern_to_date(night, month, year)


def convert_month_between_days(raw: str, year):
    string = preprocess(raw)
    match = re.match(rf"^(?P<month>{base_month_pattern})\s*[,.]?\s*(\d+)?,?\s*(?P<between>{between_days_pattern})", string)
    month, between = match.group("month"), match.group("between")
    return convert_between_days_pattern(between, month, year)


def convert_month_range(raw: str, year, code: str) -> DateRange | list[Date | DateRange]:
    match = re.match(month_range_pattern, code)
    first_month_code, second_month_code = match.group(1), match.group(3)

    # print(match.groups())
    
    first_month_converter = get_month_converter_by_code(first_month_code)
    second_month_converter = get_month_converter_by_code(second_month_code)

    string = preprocess(raw)
    first_month_string, second_month_string = re.split("\s*-\s*", string)

    first_month_date = first_month_converter(first_month_string, year)
    second_month_date = second_month_converter(second_month_string, year)

    if type(first_month_date) is list and len(first_month_date) == 1:
        first_month_date = first_month_date[0]

    if type(second_month_date) is list and len(second_month_date) == 1:
        second_month_date = second_month_date[0]

    if isinstance(first_month_date, DateRange) and isinstance(second_month_date, DateRange):
        return DateRange(first_month_date.start_date, second_month_date.end_date)
    
    if isinstance(first_month_date, DateRange) and isinstance(second_month_date, Date):
        return DateRange(
            start_date=first_month_date.start_date,
            end_date=Date.last_day_in_month(year, second_month_date.month) if second_month_date.is_month else second_month_date,
        )
    
    if isinstance(first_month_date, Date) and isinstance(second_month_date, DateRange):
        return DateRange(
            start_date=Date.first_day_in_month(year, first_month_date.month) if first_month_date.is_month else first_month_date,
            end_date=second_month_date.end_date,
        )
    
    if isinstance(first_month_date, Date) and isinstance(second_month_date, Date):
        return DateRange(
            start_date=Date.first_day_in_month(year, first_month_date.month) if first_month_date.is_month else first_month_date,
            end_date=Date.last_day_in_month(year, second_month_date.month) if second_month_date.is_month else second_month_date,
        )
    
    if type(first_month_date) is list and isinstance(second_month_date, Date):
        last_first_month_date = first_month_date[-1]

        if isinstance(last_first_month_date, Date):
            return [
                *first_month_date[:-1],
                DateRange(
                    start_date=last_first_month_date,
                    end_date=second_month_date,
                )
            ]
        else:
            raise NotImplementedError("Last date of first month list is probably a DateRange")
        
    if isinstance(first_month_date, Date) and type(second_month_date) is list:
        first_second_month_date = second_month_date[0]

        if isinstance(first_second_month_date, Date):
            return [
                DateRange(
                    start_date=first_month_date,
                    end_date=first_second_month_date,
                ),
                *second_month_date[1:],
            ]
        else:
            raise NotImplementedError("First date of second month list is probably a DateRange")
        
    if isinstance(first_month_date, list) and type(second_month_date) is list:
        last_first_month_date = first_month_date[-1]
        first_second_month_date = second_month_date[0]

        if isinstance(last_first_month_date, Date) and isinstance(first_second_month_date, Date):
            return [
                *first_month_date[:-1],
                DateRange(
                    start_date=last_first_month_date,
                    end_date=first_second_month_date,
                ),
                *second_month_date[1:],
            ]
        else:
            raise NotImplementedError("First date of second month list is probably a DateRange")
        
    raise NotImplementedError(f"Unexpected month range combination: {type(first_month_date)}, {type(second_month_date)}")


def get_month_converter_by_code(code: str) -> Callable[[], Date | DateRange | list[Date | DateRange]]:
    if re.match(r"^MD(,D)*$", code):
        code = "MD"

    match code:
        case "M":
            return convert_month_pattern_to_date
        case "MD": 
            return convert_single_month_day_or_range_sequence
        case "M%":
            return convert_month_part_or_range
        case "M>D":
            return convert_after_month_day
        case "M<D":
            return convert_before_month_day
        case "M%,<D":
            return convert_month_part_before_day
        case "M%,>D":
            return convert_month_part_after_day
        case "M~D":
            return convert_around_month_day
        case _:
            raise NotImplementedError
        

def convert_sequence_of_months(raw: str, year) -> list[Date | DateRange]:
    string = preprocess(raw)
    months = re.split(rf"\s*[,;и]\s*(?=(?:{base_month_pattern}))", string)
    return sum([convert_single_month_day_or_range_sequence(month, year) for month in months], [])
        

def convert_year_date(raw: str, year) -> DateRange:
    string = preprocess(raw)
    match = re.match(rf"(\d+)\s*({question_mark_pattern})?", string)
    date, q = match.groups()

    if int(date) != int(year):
        raise ValueError(f"Year date {date} is not equal to year {year}")
    
    range = DateRange.year(year)
    range.is_uncertain = has_value(q)
    return range


def convert_year_range(raw: str) -> DateRange:
    string = preprocess(raw)
    match = re.match(year_range_pattern, string)
    _, year_1, q_1, _, year_2, q_2 = match.groups()

    year_1_date = Date.first_day_in_year(year_1)
    year_1_date.is_uncertain = has_value(q_1)

    year_2_date = Date.last_day_in_year(year_2)
    year_2_date.is_uncertain = has_value(q_2)

    range = DateRange(year_1_date, year_2_date)
    range.is_year_range = True
    return range


def convert_season(raw: str, year) -> DateRange:
    string = preprocess(raw)
    match = re.match(rf"({season_pattern})\s*({question_mark_pattern})?", string)
    season, q = match.group(1), match.group(2)

    match season:
        case "лето":
            range = DateRange.summer(year)
        case "осень":
            range = DateRange.autumn(year)
        case _:
            raise NotImplementedError(f'Unexpected season: "{season}".')
        
    range.is_uncertain = has_value(q)
    return range

    



# def convert_year(raw: str):
#     string = preprocess(raw)
#     year = re.match(rf"^$", string)
#     month, part = match.group("month"), match.group("part")
#     return convert_part_pattern_to_date(part, month, year)





#     start_date = Date(year, month, start_day, is_uncertain=bool(start_day_q and start_day_q.strip()))
#     end_date = Date(year, month, end_day, is_uncertain=bool(end_day_q and end_day_q.strip()))
    
#     return DateRange(start_date, end_date)



# def convert_month_day_sequences_to_dates(init_string: str, year) -> list[Date | DateRange]:
#     question_mark_pattern = r"(\(\?\)|\?)"
#     day_pattern = rf"(\d+)\s*{question_mark_pattern}?"
#     day_range_pattern = rf"{day_pattern}\s*[-—]\s*{day_pattern}"
#     day_or_range_pattern = rf"({day_range_pattern}|{day_pattern})"
#     comma_pattern = rf"\s*[,и]\s*"

#     string = re.sub(r"\s+", " ", init_string.lower().strip(". "))
#     string = re.sub(r"[-—]+", "-", string)
#     string = re.sub(r"(\d+)\s+(\d+)", r"\1, \2", string)
#     string = re.sub(rf"(,\s+){question_mark_pattern}\s+({day_or_range_pattern})", r"\1\3 (?)", string)

#     months = re.split(r"\s*;\s*", string)

#     dates = []

#     for month in months:
#         month_name_match = re.search(rf"({base_month_pattern})\s*,?\s*", month)
#         month_name = month_name_match.group(1)
        
#         day_sequence = month[month_name_match.end():]
#         assert re.match(rf"{day_or_range_pattern}({comma_pattern}{day_or_range_pattern})*$", day_sequence), f"{string} /// {init_string}"

#         days = re.split(rf"{comma_pattern}", day_sequence)

#         for day in days:
#             if match := re.match(day_range_pattern, day):
#                 start_day, start_day_question, end_day, end_day_question = match.groups()
                
#                 start_date = Date(year, month_name, start_day)
#                 start_date.is_uncertain = bool(start_day_question and start_day_question.strip())

#                 end_date = Date(year, month_name, end_day)
#                 end_date.is_uncertain = bool(end_day_question and end_day_question.strip())

#                 date_range = DateRange(start_date, end_date)
#                 dates.append(date_range)
#             elif match := re.match(day_pattern, day):
#                 day, day_question = match.groups()
#                 date = Date(year, month_name, day)
#                 date.is_uncertain = bool(day_question and day_question.strip())
#                 dates.append(date)
#             else:
#                 raise NotImplementedError(f"Failed to parse {string}.")
            
#     return dates






#     re.match(rf"\s*{base_month_pattern}\s*")
#     month_name = re.search(rf"{base_month_pattern}").group()

#     re.findall(r"\d+\s*(\(\?\)|\?)")
