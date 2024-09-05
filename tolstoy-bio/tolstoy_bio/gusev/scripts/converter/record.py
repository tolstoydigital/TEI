from dataclasses import dataclass

import bs4


@dataclass
class Record:
    source_path: str
    index: int
    soup: bs4.BeautifulSoup

    def __repr__(self) -> str:
        return f'Record #{self.index} in "{self.source_path}"'