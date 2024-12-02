from dataclasses import dataclass

from .gusev_source_type import GusevSourceType


@dataclass
class GusevBiblTextSegment:
    text: str

    def get_text(self) -> str:
        return self.text

    def get_source_types(self) -> list[GusevSourceType]:
        detected_types: list[GusevSourceType] = []

        if self.text.startswith(f"Д "):
            detected_types.append(GusevSourceType.TOLSTOY_DIARY)

        if "ДСТ" in self.text:
            detected_types.append(GusevSourceType.TOLSTAYA_DIARY)

        if "ЕСТ" in self.text:
            detected_types.append(GusevSourceType.TOLSTAYA_JOURNAL)

        if "ЯЗ" in self.text:
            detected_types.append(GusevSourceType.MAKOVITSKY)

        if "Гольд" in self.text:
            detected_types.append(GusevSourceType.GOLDENWEISER)

        if "Юб." in self.text:
            detected_types.append(GusevSourceType.TOLSTOY_LETTER)

        return detected_types
