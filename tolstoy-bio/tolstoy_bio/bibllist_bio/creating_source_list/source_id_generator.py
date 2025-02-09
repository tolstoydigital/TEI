import re
from string import ascii_lowercase as latin_alphabet_letters

from transliterate import translit

from tolstoy_bio.bibllist_bio.creating_source_list.source import Source
from tolstoy_bio.utilities.function import FunctionUtils


def transliterate_cyrillic_text(text: str) -> str:
    return translit(text, "ru", reversed=True)


def remove_soft_sign_transliterations(text: str) -> str:
    return re.sub(r"'", "", text)


def replace_non_alphanumeric_characters_with_space(text: str):
    return re.sub(r"[^a-zA-Z0-9а-яёА-ЯЁ]", " ", text)


def trim_space_sequences(string: str):
    return re.sub("\s+", " ", string).strip()


def join_strings_by_space(strings: list[str]):
    return " ".join(strings)


def convert_items_to_strings(items: list):
    return [str(item) for item in items]


def replace_spaces_with_underscores(string: str):
    return re.sub("\s+", "_", string)


class SourceIdGenerator:
    _generated_id_counts: dict[str, int]

    def __init__(self):
        self._generated_id_counts = {}

    def generate(self, source: Source) -> str:
        try:
            return self._generate_unique_id_from_source(source)
        except AssertionError as e:
            return f"NONE: {source.index}"

    def _generate_unique_id_from_source(self, source: Source) -> str:
        base_id = self._generate_base_id_from_source(source)

        duplicate_count = self._generated_id_counts.get(base_id, 0)

        if duplicate_count > 0:
            duplicate_count_to_be = duplicate_count + 1
            unique_id = self._make_id_unique(base_id, duplicate_count_to_be)

            self._generated_id_counts[base_id] = duplicate_count_to_be

            return unique_id

        self._generated_id_counts[base_id] = 1
        return base_id

    @classmethod
    def _generate_base_id_from_source(cls, source: Source) -> str:
        components = [
            source.author,
            "Былое" if source.index == "66" else (source.work or source.anthology),
            source.publication_date,
        ]

        existent_components = [component for component in components if component]

        if len(existent_components) == 0 or (
            len(existent_components) == 1
            and existent_components[0] == source.publication_date
        ):
            raise AssertionError(
                f"Insufficient number of components to generate the semantic id for {source}"
            )

        return cls._generate_base_id_from_components(*existent_components)

    @staticmethod
    def _generate_base_id_from_components(*components: tuple[str]) -> str:
        return FunctionUtils.pipe(
            components,
            (
                convert_items_to_strings,
                join_strings_by_space,
                replace_non_alphanumeric_characters_with_space,
                trim_space_sequences,
                transliterate_cyrillic_text,
                replace_spaces_with_underscores,
                remove_soft_sign_transliterations,
            ),
        )

    def _make_id_unique(self, base_id: str, count_to_be: int):
        postfix_letter_index = count_to_be - 2

        assert postfix_letter_index < len(latin_alphabet_letters), (
            f"Invalid count to be: {count_to_be}, "
            f"there are only {len(latin_alphabet_letters)} letters in the latin alphabet {self._generated_id_counts}"
        )

        postfix_letter = latin_alphabet_letters[postfix_letter_index]

        return f"{base_id}_{postfix_letter}"
