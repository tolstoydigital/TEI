from enum import Enum, auto


class GusevSourceType(Enum):
    TOLSTOY_DIARY = auto()
    TOLSTOY_DIARY_WITH_PARENTHESIS_PREFIX = auto()
    TOLSTAYA_DIARY = auto()
    TOLSTAYA_JOURNAL = auto()
    MAKOVITSKY = auto()
    GOLDENWEISER = auto()
    TOLSTOY_LETTER = auto()


class GusevSourceTypeUtils:
    @staticmethod
    def get_code_by_type(type: GusevSourceType) -> str:
        return {
            GusevSourceType.TOLSTOY_DIARY: "Д",
            GusevSourceType.TOLSTAYA_DIARY: "ДСТ",
            GusevSourceType.TOLSTAYA_JOURNAL: "ЕСТ",
            GusevSourceType.MAKOVITSKY: "ЯЗ",
            GusevSourceType.GOLDENWEISER: "Гольд",
            GusevSourceType.TOLSTOY_LETTER: "Юб.",
        }[type]
