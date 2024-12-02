from dataclasses import dataclass
from enum import StrEnum

import bs4


class GusevSourceCode(StrEnum):
    TOLSTOY_DIARY = "Д"
    TOLSTAYA_DIARY = "ДСТ"
    TOLSTAYA_JOURNAL = "ЕСТ"
    MAKOVITSKY = "ЯЗ"
    GOLDENWEISER = "Гольд"
    TOLSTOY_LETTER = "Юб."


@dataclass
class GusevBiblTextSegment:
    text: str


@dataclass
class GusevBiblText:
    text: str

    def get_segments(self) -> list[GusevBiblTextSegment]:
        segments = self.text.split(";")
        stripped_segments = [segment.strip() for segment in segments]
        return [GusevBiblTextSegment(text=segment) for segment in stripped_segments]


@dataclass
class GusevBiblElement:
    element: bs4.Tag

    def get_text(self) -> GusevBiblText:
        return GusevBiblText(text=self.element.text.strip())
