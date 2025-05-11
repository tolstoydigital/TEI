from bs4 import Tag


class SourceListEntry:
    _tag: Tag

    def __init__(self, tag: Tag):
        self._tag = tag

    def get_tag(self) -> Tag:
        return self._tag

    def get_id(self) -> str:
        return self._tag.attrs["xml:id"]

    def get_main_title(self) -> str | None:
        tag = self._tag.find("title", {"type": "main"})

        if not tag:
            return None

        return tag.text.strip()

    def get_bibliographic_title(self) -> str | None:
        tag = self._tag.find("title", {"type": "bibl"})

        if not tag:
            return None

        return tag.text.strip()
