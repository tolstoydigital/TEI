from functools import lru_cache, wraps
from itertools import chain
import os
import re
from typing import Generator
from uuid import uuid4

import bs4
from tqdm import tqdm

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils
from tolstoy_bio.utilities.xml import XmlUtils


BIBLLIST_BIO_PATH = os.path.join(
    os.path.dirname(__file__), "../../../reference/bibllist_bio.xml"
)


TOLSTOY_DIARIES_REPOSITORY_PATH = os.path.join(
    os.path.dirname(__file__), "../../../texts/diaries"
)


TOLSTAYA_LETTERS_REPOSITORY_PATH = os.path.join(
    os.path.dirname(__file__), "../tolstaya_letters/data/xml"
)


class RelatedItem:
    def __init__(self, soup: bs4.Tag):
        self._soup = soup

    def get_document_id(self) -> str:
        return self._soup.find("ref", {"xml:id": True}).attrs["xml:id"].strip()

    def get_opener_text(self) -> str:
        return self._get_opener().text.strip()

    def set_opener_text(self, text: str) -> None:
        opener = self._get_opener()

        assert BeautifulSoupUtils.has_only_navigable_string(opener)

        new_opener_string = bs4.BeautifulSoup("", "xml").new_string(text)
        opener.string.replace_with(new_opener_string)

    def _get_opener(self) -> bs4.Tag:
        return self._soup.find("opener")


class Item:
    def __init__(self, soup: bs4.Tag):
        self._soup = soup

    @lru_cache
    def get_id(self) -> str:
        return self._soup.find("ref", {"xml:id": True}).attrs["xml:id"].strip()

    def get_related_items(self) -> list[RelatedItem]:
        return [RelatedItem(element) for element in self._soup.find_all("relatedItem")]


class BibllistBio:
    def __init__(self, path: str):
        soup = BeautifulSoupUtils.create_soup_from_file(path, "xml")
        self._soup = soup
        self._path = path

    def _get_item_by_id(self, id_: str) -> Item:
        element = self._soup.find("ref", {"xml:id": id_}).parent
        return Item(element)

    def get_tolstoy_diaries_item(self) -> Item:
        return self._get_item_by_id("Tolstoy_diaries")

    def get_tolstaya_letters_item(self) -> Item:
        return self._get_item_by_id("SAT_letters")

    def save(self) -> None:
        BeautifulSoupUtils.prettify_and_save(self._soup, self._path)


class TeiDocument:
    _path: str
    _soup: bs4.BeautifulSoup

    def __init__(self, path: str) -> None:
        self._path = path
        self._soup = None

    def get_path(self) -> str:
        return self._path

    def get_id(self) -> str:
        filename = os.path.basename(self._path)
        return filename.replace(".xml", "")

    def load(self) -> bs4.BeautifulSoup:
        self._soup = BeautifulSoupUtils.create_soup_from_file(self._path, "xml")
        return self._soup

    def _with_loading(func):
        @wraps(func)
        def method(self, *args, **kwargs):
            if self._soup is None:
                self.load()

            return func(self, *args, **kwargs)

        return method

    def _assert(self, condition: bool, error_message: str) -> None:
        assert condition, f"{error_message} at {self._path}"

    @_with_loading
    def get_opener_elements(self) -> bs4.Tag | None:
        return self._soup.find_all("opener")

    @_with_loading
    def get_as_inline_string(self) -> str:
        return BeautifulSoupUtils.inline_prettify(self._soup)

    @_with_loading
    def get_as_string(self) -> str:
        return self._soup.prettify()

    def save(self, content: str | None = None) -> None:
        if content:
            soup = bs4.BeautifulSoup(content, "xml")
            BeautifulSoupUtils.prettify_and_save(soup, self._path)
            return

        if not self._soup:
            self.load()

        BeautifulSoupUtils.prettify_and_save(self._soup, self._path)


class DocumentRepository:
    def __init__(self, repository_path: str):
        self._repository_path = repository_path

    def get_documents(self) -> Generator[TeiDocument, None, None]:
        for folder_path, _, filenames in os.walk(self._repository_path):
            if not filenames:
                continue

            for filename in filenames:
                if filename == "template.xml":
                    continue

                if "__pycache__" in folder_path:
                    continue

                if not filename.endswith(".xml"):
                    continue

                path = os.path.join(folder_path, filename)
                yield TeiDocument(path)


class TolstoyDiariesRepository(DocumentRepository):
    def __init__(self):
        super().__init__(TOLSTOY_DIARIES_REPOSITORY_PATH)


class TolstayaLettersRepository(DocumentRepository):
    def __init__(self):
        super().__init__(TOLSTAYA_LETTERS_REPOSITORY_PATH)


def remove_braces_from_bibllist_bio_openers():
    print("Loading bibllist_bio.xml data...")

    bibllist = BibllistBio(BIBLLIST_BIO_PATH)

    tolstoy_diaries_item = bibllist.get_tolstoy_diaries_item()
    tolstaya_letters_item = bibllist.get_tolstaya_letters_item()

    for item in [tolstoy_diaries_item, tolstaya_letters_item]:
        for related_item in tqdm(item.get_related_items(), item.get_id()):
            opener_text = related_item.get_opener_text()

            if "[" not in opener_text or "]" not in opener_text:
                continue

            updated_opener_text = re.sub(r"[\[\]]", "", opener_text)
            updated_opener_text = re.sub(r"\s+", " ", updated_opener_text)
            related_item.set_opener_text(updated_opener_text)

    print("Saving bibllist_bio.xml...")

    bibllist.save()


def replace_square_braces_with_tags():
    print("Replacing square brackets with tags...")

    tolstoy_diaries_repository = TolstoyDiariesRepository()
    tolstaya_letters_repository = TolstayaLettersRepository()

    replace_square_braces_with_tags_for_repository(
        tolstoy_diaries_repository, "tolstoy-diaries"
    )

    replace_square_braces_with_tags_for_repository(
        tolstaya_letters_repository, "tolstaya-letters"
    )

    documents = chain(
        tolstoy_diaries_repository.get_documents(),
        tolstaya_letters_repository.get_documents(),
    )

    for document in tqdm(list(documents), "Validating XML"):
        validate_xml_or_fail(document.get_as_string())


def replace_square_braces_with_tags_for_repository(
    repository: DocumentRepository, key: str
) -> str:
    for document in tqdm(list(repository.get_documents()), key):
        content = document.get_as_inline_string()
        opener_matches = list(re.finditer(r"<opener[^<]*>.*?</opener>", content))

        for opener_match in opener_matches[::-1]:
            opener_text = opener_match.group(0)

            opener_text_with_handled_close_braces = (
                replace_close_square_braces_with_tags(opener_text)
            )

            opener_text_with_handled_distant_braces = (
                replace_distant_square_braces_with_tags(
                    opener_text_with_handled_close_braces
                )
            )

            opener_start_index, opener_end_index = opener_match.span()

            content_with_distant_tags = (
                content[:opener_start_index]
                + opener_text_with_handled_distant_braces
                + content[opener_end_index:]
            )

            try:
                validate_xml_or_fail(content_with_distant_tags)
                content = content_with_distant_tags
            except:
                print(f"Avoiding XML syntax errors for {document.get_path()}")

                content = (
                    content[:opener_start_index]
                    + opener_text_with_handled_close_braces
                    + content[opener_end_index:]
                )

        document.save(content)


def replace_close_square_braces_with_tags(opener_text: str) -> str:
    return re.sub(
        r"\[([^\[\<\>]*)\](?![^<]*>)",
        r'<add resp="volume_editor">\1</add>',
        opener_text,
    )


def replace_distant_square_braces_with_tags(opener_text: str) -> str | None:
    return re.sub(
        r"\[([^\]]+)\](?![^<]*>)",
        r'<add resp="volume_editor">\1</add>',
        opener_text,
    )


def validate_xml_or_fail(content: str) -> None:
    content_to_validate = re.sub(
        r'xml:id=".*?"',
        lambda m: f'xml:id="a{uuid4()}"',
        content,
    )

    XmlUtils.validate_xml_or_fail(content_to_validate)


# def reformat_tolstoy_diaries():
#     """
#     Script to prettify Tolstoy's diaries
#     for easier manual validation using Git
#     """
#     tolstoy_diaries_repository = TolstoyDiariesRepository()

#     for document in tqdm(
#         list(tolstoy_diaries_repository.get_documents()),
#         "Reformatting Tolstoy's diaries",
#     ):
#         document.save()


def main():
    # reformat_tolstoy_diaries()
    remove_braces_from_bibllist_bio_openers()
    replace_square_braces_with_tags()

    print("Done!")


# Below is the draft script for replacing square brackets with <add/> tags
# handling the cases where the content within brackets has nested tags.
# So far, a simpler approach implemented in replace_square_braces_with_tags function
# is preferred: cases where the content within brackets has nested tags are ignored.

# def __replace_square_braces_with_tags():
#     tolstoy_diaries_repository = TolstoyDiariesRepository()
#     tolstaya_letters_repository = TolstayaLettersRepository()

#     for document in tqdm(
#         list(tolstoy_diaries_repository.get_documents()), disable=True
#     ):
#         try:
#             content = document.get_as_inline_string()

#             opener_match = re.search(r"<opener[^<]*>.*?</opener>", content)

#             if not opener_match:
#                 continue

#             opener_with_add_elements = re.sub(
#                 r"\[([^\]]+)\](?![^<]*>)",
#                 r'<add resp="volume_editor">\1</add>',
#                 opener_match.group(0),
#             )

#             opener_start_index, opener_end_index = opener_match.span()

#             content_with_add_elements = (
#                 content[:opener_start_index]
#                 + opener_with_add_elements
#                 + content[opener_end_index:]
#             )

#             from uuid import uuid4

#             content_with_add_elements = re.sub(
#                 r'xml:id=".*?"',
#                 lambda m: f'xml:id="a{uuid4()}"',
#                 content_with_add_elements,
#             )

#             XmlUtils.validate_xml_or_fail(content_with_add_elements)
#         except Exception as e:
#             print(document._path)
#             # print(opener_with_add_elements)
#             # raise e

#         continue

#         opener_elements = document.get_opener_elements()

#         if len(opener_elements) == 0:
#             continue

#         opener_element = opener_elements[0]

#         opener_text = re.sub(r"\s+", " ", opener_element.text.strip())

#         if re.search(r"\[[\]]*\[", opener_text) or re.search(r"\][\[]*\]", opener_text):
#             print(opener_text)

#         # if not validate_braces(opener_text):
#         #     continue

#         # if re.search(r"\[[^\[]*\]", opener_text) and (
#         #     opener_text.count("[") != 1 or opener_text.count("]") != 1
#         # ):
#         #     print(opener_text)

#         # if re.search(r"\[[^\[]*\]", opener_text):
#         #     print(opener_text)

#     # print("Saving bibllist_bio.xml...")

#     # bibllist.save()

#     # print("Done!")


# def validate_braces(string: str) -> bool:
#     stack = 0

#     for character in string:
#         if character == "[":
#             stack += 1
#         elif character == "]":
#             stack -= 1

#         if stack < 0:
#             return False

#     return stack == 0


# def create_string(text: str) -> bs4.NavigableString:
#     return bs4.BeautifulSoup(features="xml").new_string(text)


# def create_tag(*args, **kwargs) -> bs4.Tag:
#     return bs4.BeautifulSoup(features="xml").new_tag(*args, **kwargs)


# def create_add_element() -> bs4.Tag:
#     return create_tag("add", attrs={"resp": "volume_editor"})


# def replace(opener_element: bs4.Tag) -> None:
#     for descendant in list(opener_element.descendants):
#         if type(descendant) is not bs4.NavigableString:
#             continue

#         string = str(descendant)

#         if "[" not in string and "]" not in string:
#             continue

#         fully_braced_matches = list(re.finditer(r"^\[([^\[]*)\]", string))

#         if fully_braced_matches:
#             new_descendant_children = []

#             new_descendant_children.append(
#                 create_string(string[: fully_braced_matches[0].start])
#             )

#             for match in fully_braced_matches:
#                 new_descendant_children.append(create_string(string[: match.start]))

#                 add_element = create_add_element()

#                 if match.group(1) != "":
#                     add_element.string = match.group(1)

#                 new_descendant_children.append(add_element)

#             new_descendant_children.append(string[fully_braced_matches[-1].end :])

#             descendant.replace_with(new_descendant_children)
#             return

#         # new_parent_children = []

#         # new_children = []

#         # for match in re.search(r"^\[([^\[]*)\]", str(string)):

#         # if match := re.search(r"^\[[^\[]+\]", str(string)):
#         #     parent = string.parent

#         print(string)
#         print()
#         print("-----")
#         print()


# def get_deep_navigable_strings_(element: bs4.Tag) -> list[bs4.NavigableString]:
#     children = []

#     for descendant in element.descendants:
#         if type(descendant) is bs4.NavigableString:
#             children.append(descendant)

#     return children


# def get_deep_navigable_strings(element: bs4.Tag) -> list[bs4.NavigableString]:
#     children = []

#     def _collect_children(element: bs4.Tag):
#         for child in element.children:
#             if type(child) is bs4.Tag:
#                 _collect_children(child)
#             elif type(child) is bs4.NavigableString:
#                 children.append(child)

#     _collect_children(element)
#     return children


if __name__ == "__main__":
    main()
