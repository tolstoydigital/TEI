"""
Скрипт применяет к XML-документам внутри texts
правила оборачивания фрагментов XML-документов в <p> с присвоением UUID,
взятые из скрипта формирования texts_front.xml c некоторыми расширениями.

-------------

Скрипт следует запускать, находясь в папке данного модуля,
для правильного разрешения путей к файлам и каталогам.

Версия Python: 3.11.5

Внешние библиотеки:
- beautifulsoup4
- tqdm
"""

from copy import deepcopy
import os
from pprint import pprint
import uuid

import bs4
from tqdm import tqdm


class UuidGenerator:
    """
    Генератор UUID с проверкой дубликатов относительно множества uuids.
    """

    def __init__(self, uuids: set[str] = None):
        self._uuids = deepcopy(uuids) if uuids else set()

    def generate_unique_uuid(self):
        uuid = self._generate_unique_uuid()
        self._uuids.add(uuid)
        return uuid

    def _generate_unique_uuid(self):
        while True:
            uuid = self._generate_uuid()

            if uuid in self._uuids:
                continue

            return uuid
        
    @staticmethod
    def _generate_uuid():
        return str(uuid.uuid4())


class DocumentProcessor:
    """
    Обработчик XML-контента:
    - собирает все UUID элементов;
    - оборачивает фрагменты в <p> согласно правилам.
    """

    UUID_ATTRIBUTE_NAME = "id"
    UUID_CARRYING_TAGS = ["p", "l"]
    ELEMENTS_THAT_SHOULD_NOT_BE_WRAPPED_IN_P = set([
        "p", 
        "l", 
        "lg", 
        "noteGrp", 
        "div", 
        "table", 
        "cit", 
        "row", 
        "cell", 
        "tr", 
        "td", 
        "div1", 
        "bibl",
        "figure",
        "epigraph",
        "quote",
        "del",
    ])

    def __init__(self, document_content: str):
        self._soup = bs4.BeautifulSoup(document_content, "xml")

    @classmethod
    def from_path(cls, document_path: str):
        with open(document_path, "r") as file:
            content = file.read()
            return cls(content)
        
    def get_formatted_content(self):
        return self._soup.prettify()
    
    def save_formatted_content_to_file(self, path: str):
        with open(path, "w") as file:
            file.write(self.get_formatted_content())

    def get_all_uuids(self) -> list[str]:
        uuids = []

        for tag in self._get_id_receiving_tags():
            uuid = tag.attrs.get(self.UUID_ATTRIBUTE_NAME, None)

            if uuid:
                uuids.append(uuid)
        
        return uuids

    def add_p_wrappers_where_appropriate(self) -> None:
        body = self._soup.find("body")

        for tag in body.find_all():
            if self._should_not_wrap_in_p(tag):
                continue

            if self._is_direct_div_child_of_body(tag, body):
                continue

            if self._is_direct_child_of_parent(tag, "noteGrp"):
                continue

            if self._has_parent_with_tag_name(tag, *self.UUID_CARRYING_TAGS):
                continue

            self._wrap_tag_in_p(tag)

    def add_missing_ids_to_uuid_carrying_tags(self, uuid_generator: UuidGenerator = None):
        if uuid_generator is None:
            uuid_generator = UuidGenerator()

        for tag in self._get_id_receiving_tags():
            if self._get_uuid_of_tag(tag) is None:
                uuid = uuid_generator.generate_unique_uuid()
                self._set_uuid_to_tag(uuid, tag)

    def change_paragraphs_to_spans_within_notes(self):
        for note in self._soup.find_all("note"):
            for paragraph in note.find_all("p"):
                if self._has_parent_with_tag_name(paragraph, "p"):
                    paragraph.name = "span"
                    paragraph.attrs["data-class"] = "paragraph"

    def validate_nesting(self, message):
        outputs = {}

        for tag in self._soup.find_all("p"):
            if self._has_parent_with_tag_name(tag, "p"):
                outputs[
                    f"Found <p> nested in <p>. Tag parent is {tag.parent.name if tag.parent else 'unknown'}"
                ] = message

            if self._has_parent_with_tag_name(tag, "l"):
                outputs[
                    f"Found <p> nested in <l>. Tag parent is {tag.parent.name if tag.parent else 'unknown'}"
                ] = message

        for tag in self._soup.find_all("l"):
            if self._has_parent_with_tag_name(tag, "p"):
                outputs[
                    f"Found <l> nested in <p>. Tag parent is {tag.parent.name if tag.parent else 'unknown'}"
                ] = message

            if self._has_parent_with_tag_name(tag, "l"):
                outputs[
                    f"Found <l> nested in <l>. Tag parent is {tag.parent.name if tag.parent else 'unknown'}"
                ] = message

        return outputs

    def _get_id_receiving_tags(self) -> list[bs4.Tag]:
        return self._soup.find_all(self.UUID_CARRYING_TAGS)
    
    def _get_uuid_of_tag(self, tag: bs4.Tag) -> str | None:
        return tag.attrs.get(self.UUID_ATTRIBUTE_NAME, None)
    
    def _set_uuid_to_tag(self, uuid: str, tag: bs4.Tag) -> None:
        tag.attrs[self.UUID_ATTRIBUTE_NAME] = uuid

    def _should_not_wrap_in_p(self, tag: bs4.Tag) -> bool:
        return tag.name in self.ELEMENTS_THAT_SHOULD_NOT_BE_WRAPPED_IN_P

    def _get_body(self):
        return self._soup.find("body")

    def _is_direct_div_child_of_body(self, tag: bs4.Tag, body: bs4.Tag = None) -> bool:
        if body is None:
            body = self._get_body()
            
        return tag.name == "div" and tag.parent is body

    def _is_direct_child_of_parent(self, potential_child: bs4.Tag, potential_parent_name: str) -> bool:
        real_parent = potential_child.parent
        return real_parent and real_parent.name == potential_parent_name
    
    def _has_parent_with_tag_name(self, element: bs4.BeautifulSoup, *tag_names: list[str]) -> bool:
        parent = element.parent
        target_tag_names = set(tag_names)

        while parent:
            if isinstance(parent, bs4.Tag) and parent.name in target_tag_names:
                return True
            
            parent = parent.parent

        return False

    def _wrap_tag_in_p(self, tag: bs4.Tag):
        self._wrap(tag, "p")

    def _wrap(self, tag: bs4.Tag, *wrapper_args, **wrapper_kwargs):
        return tag.wrap(self._create_tag(*wrapper_args, **wrapper_kwargs))

    def _create_tag(self, *args, **kwargs):
        return self._soup.new_tag(*args, **kwargs)


VOLUMINOUS_TEXTS_REPOSITORY_PATH = "../texts"


def main():
    print("Building UUID generator ...")
    uuid_generator = get_uuid_generator()

    print("Processing XML documents ...")
    error_messages_to_document_paths = {}
    for path in traverse_xml_documents(VOLUMINOUS_TEXTS_REPOSITORY_PATH, verbose=True):
        processor = DocumentProcessor.from_path(path)
        processor.add_p_wrappers_where_appropriate()
        processor.add_missing_ids_to_uuid_carrying_tags(uuid_generator)
        processor.change_paragraphs_to_spans_within_notes()
        error_messages_to_document_paths.update(processor.validate_nesting(path))
        processor.save_formatted_content_to_file(path)
    
    print("Done!\n")
    print("Validation results:")
    pprint(error_messages_to_document_paths)


def check_if_all_uuids_are_unique():
    all_uuids = set()

    for path in traverse_xml_documents(VOLUMINOUS_TEXTS_REPOSITORY_PATH, verbose=True):
        processor = DocumentProcessor.from_path(path)
        uuids = processor.get_all_uuids()
        assert all_uuids.isdisjoint(set(uuids)), f"Duplicate UUIDs found in {path}."
        all_uuids.update(uuids)


def traverse_xml_documents(folder_path: str, *, verbose: bool = False):
    """
    Итерируется рекурсивно по всем XML-файлам в папке folder_path,
    возвращая путь к файлу на каждой итерации.
    """
    for path, _, files in os.walk(folder_path):
        file_iterator = tqdm(files, desc=f"Traversing files in {path}") if verbose else files
        
        for filename in file_iterator:
            if not filename.endswith(".xml"):
                continue

            yield os.path.join(path, filename)


def get_uuid_generator() -> UuidGenerator:
    """
    Собирает все UUID элементов texts-документов
    и возвращает генератор UUID.
    """
    all_uuids = set()

    for path in traverse_xml_documents(VOLUMINOUS_TEXTS_REPOSITORY_PATH, verbose=True):
        processor = DocumentProcessor.from_path(path)
        uuids = processor.get_all_uuids()
        all_uuids.update(uuids)

    return UuidGenerator(all_uuids)


if __name__ == "__main__":
    main()