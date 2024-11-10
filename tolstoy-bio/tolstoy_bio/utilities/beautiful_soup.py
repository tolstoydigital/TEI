from typing import Callable

import bs4

from tolstoy_bio.utilities.io import IoUtils


class BeautifulSoupUtils:
    @staticmethod
    def create_soup_from_file(file_path: str, parser: str, encoding: str = None) -> bs4.BeautifulSoup:
        file_contents = IoUtils.read_as_text(file_path, encoding)
        return bs4.BeautifulSoup(file_contents, parser)

    @staticmethod
    def get_next_tag_sibling(element: bs4.BeautifulSoup) -> bs4.Tag | None:
        output = element.next_sibling

        while output is not None and not isinstance(output, bs4.Tag):
            output = output.next_sibling

        return output
    
    @classmethod
    def for_each_next_tag_sibling(cls, element: bs4.BeautifulSoup, processor: Callable[[bs4.Tag], None]):
        current_tag_sibling = cls.get_next_tag_sibling(element)

        while current_tag_sibling is not None:
            next_tag_sibling = cls.get_next_tag_sibling(current_tag_sibling)
            processor(current_tag_sibling)
            current_tag_sibling = next_tag_sibling
    
    @staticmethod
    def get_next_tag_element(element: bs4.BeautifulSoup) -> bs4.Tag | None:
        output = element.next_element

        while output is not None and not isinstance(output, bs4.Tag):
            output = output.next_element

        return output
    
    @classmethod
    def for_each_next_tag_element(cls, element: bs4.BeautifulSoup, processor: Callable[[bs4.Tag], None]):
        current_tag_element = cls.get_next_tag_element(element)

        while current_tag_element is not None:
            next_tag_element = cls.get_next_tag_element(current_tag_element)
            processor(current_tag_element)
            current_tag_element = next_tag_element

    @staticmethod
    def is_tag(element: bs4.BeautifulSoup) -> bool:
        return isinstance(element, bs4.Tag)

    @classmethod
    def get_first_tagged_child(cls, element: bs4.BeautifulSoup) -> bs4.Tag | None:
        if not isinstance(element, bs4.Tag):
            return None

        for child in element.children:
            if cls.is_tag(child):
                return child
        
        return None
    
    @classmethod
    def has_parent_with_tag_name(cls, element: bs4.BeautifulSoup, *tag_names: list[str]) -> bool:
        parent = element.parent
        target_tag_names = set(tag_names)

        while parent:
            if isinstance(parent, bs4.Tag) and parent.name in target_tag_names:
                return True
            
            parent = parent.parent

        return False
    
    @classmethod
    def get_closest_ancestor_with_tag_name(cls, element: bs4.BeautifulSoup, tag_name: str) -> bs4.Tag:
        ancestor = element.parent

        while ancestor:
            if isinstance(ancestor, bs4.Tag) and ancestor.name == tag_name:
                return ancestor
            
            ancestor = ancestor.parent

        return None
        
    @staticmethod
    def set_inner_text(element: bs4.BeautifulSoup, content: str):
        if element.string:
            element.string.replace_with(content)
        else:
            element.append(content)

    @staticmethod
    def inline_prettify(soup: bs4.BeautifulSoup) -> str:
        prettified_soup = soup.prettify()
        stripped_lines = [line.strip() for line in prettified_soup.split("\n")]
        return "".join(stripped_lines)
    
    @staticmethod
    def decompose(*elements: list[bs4.Tag]) -> None:
        for element in elements:
            element.decompose()

    @staticmethod
    def find_if_single_or_fail(soup: bs4.BeautifulSoup, *args, **kwargs) -> bs4.Tag:
        elements = list(soup.find_all(*args, **kwargs))

        if len(elements) != 1:
            raise ValueError(
                f"Expected exactly one element matching {args}, {kwargs}, found {len(elements)}"
            )

        return elements[0]

    @staticmethod
    def has_only_navigable_string(tag: bs4.Tag) -> bool:
        children = list(tag.children)
        return len(children) == 1 and children[0] is tag.string

    @classmethod
    def get_first_navigable_string(
        cls, node: bs4.Tag | bs4.NavigableString | None
    ) -> bs4.NavigableString | None:
        if node is None:
            return None

        if isinstance(node, bs4.NavigableString):
            return node

        children = list(node.children)

        if not children:
            return None

        first_child = children[0]

        if isinstance(first_child, bs4.NavigableString):
            return first_child

        if isinstance(first_child, bs4.Tag):
            return cls.get_first_navigable_string(first_child)

        raise ValueError(f"Unexpected child type encountered: {type(first_child)}")

    @classmethod
    def get_last_navigable_string(
        cls, node: bs4.Tag | bs4.NavigableString | None
    ) -> bs4.NavigableString | None:
        if node is None:
            return None
        
        if isinstance(node, bs4.NavigableString):
            return node

        children = list(node.children)

        if not children:
            return None

        last_child = children[-1]

        if isinstance(last_child, bs4.NavigableString):
            return last_child

        if isinstance(last_child, bs4.Tag):
            return cls.get_last_navigable_string(last_child)

        raise ValueError(f"Unexpected child type encountered: {type(last_child)}")

    @staticmethod
    def prettify_and_save(soup: bs4.BeautifulSoup, path: str) -> None:
        content = soup.prettify()
        IoUtils.save_textual_data(content, path)
