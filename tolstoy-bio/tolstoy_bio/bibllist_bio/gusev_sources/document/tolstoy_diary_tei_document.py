from datetime import datetime, timedelta
import os
import bs4

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils


def convert_range_to_dates(start_date_str, end_date_str) -> list[str]:
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

    dates_list = []

    current_date = start_date
    while current_date <= end_date:
        dates_list.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)

    return dates_list


class TolstoyDiaryTeiDocument:
    _path: str
    _soup: bs4.BeautifulSoup | None = None

    def __init__(self, path: str):
        self._path = path

    def _assert(self, condition: bool, error_message: str):
        assert condition, f"{error_message} at {self._path}"

    def _get_soup(self) -> bs4.BeautifulSoup:
        if self._soup is None:
            self._soup = BeautifulSoupUtils.create_soup_from_file(self._path, "xml")

        return self._soup

    def get_path(self) -> str:
        return self._path

    def get_id(self) -> str:
        return os.path.basename(self._path).replace(".xml", "")

    def get_creation_dates(self) -> list[str]:
        date_element = self._get_soup().find("creation").find("date")

        if "when" in date_element.attrs:
            return [date_element.attrs["when"]]

        if all(attribute in date_element.attrs for attribute in ["from", "to"]):
            start_date = date_element.attrs["from"]
            end_date = date_element.attrs["to"]
            
            assert start_date and end_date

            try:
                return convert_range_to_dates(
                    date_element.attrs["from"], date_element.attrs["to"]
                )
            except Exception:
                return []

        return []
