import bs4


class TeiNote:
    def __init__(self, link: bs4.Tag, note: bs4.Tag):
        self._link = link
        self._note = note

    def _get_link_text(self) -> str:
        return self._link.text.strip()

    def get_link_soup(self) -> bs4.Tag:
        return self._link

    def get_note_soup(self) -> bs4.Tag:
        return self._note

    def get_string_before_link(self) -> bs4.NavigableString:
        link_previous_sibling = self._link.previous_sibling

        assert (
            type(link_previous_sibling) is bs4.NavigableString
        ), "Element before <ref> is not a string."

        return link_previous_sibling

    def get_parent(self) -> bs4.Tag:
        assert (
            self._link.parent is self._note.parent
        ), "<ref> and <note> have different parents."

        parent = self._link.parent

        assert parent, "Footnote doesn't have a parent."

        return parent

    def has_numeric_link(self) -> bool:
        link_text = self._get_link_text()
        return link_text.isdigit()

    def set_id(self, new_id: str) -> None:
        self._link.attrs["target"] = f"#{new_id}"
        self._note.attrs["xml:id"] = new_id

    def set_link_text(self, new_text: str) -> None:
        self._link.clear()
        self._link.string = new_text

    def add_footnote_type(self) -> None:
        self._note.attrs["type"] = "footnote"

    def remove_footnote_type(self) -> None:
        if "type" in self._note.attrs and self._note.attrs["type"] == "footnote":
            del self._note.attrs["type"]
