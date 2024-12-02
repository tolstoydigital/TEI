from dataclasses import dataclass

from .gusev_bibl_text_segment import GusevBiblTextSegment


@dataclass
class GusevBiblText:
    text: str

    def get_segments(self) -> list[GusevBiblTextSegment]:
        segments = self.text.split(";")
        stripped_segments = [segment.strip() for segment in segments]
        return [GusevBiblTextSegment(text=segment) for segment in stripped_segments]