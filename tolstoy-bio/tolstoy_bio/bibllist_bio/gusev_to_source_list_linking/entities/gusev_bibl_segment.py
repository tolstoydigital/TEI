from __future__ import annotations
from typing import TYPE_CHECKING

from bs4 import Tag

from ...gusev_sources.document.gusev_bibl_text_segment import GusevBiblTextSegment

if TYPE_CHECKING:
    from .gusev_tei_document import GusevTeiDocument


class GusevBiblSegment:
    _tag: Tag
    _gusev_tei_document: GusevTeiDocument

    def __init__(self, tag: Tag, gusev_tei_document: GusevTeiDocument):
        self._tag = tag
        self._gusev_tei_document = gusev_tei_document

    def get_tag(self) -> Tag:
        return self._tag

    def get_tei_document(self) -> GusevTeiDocument:
        return self._gusev_tei_document

    def get_text(self) -> str:
        return self._tag.text.strip()

    def get_id(self) -> str:
        return self._tag.attrs["id"]

    def get_parent_bibl_id(self) -> str:
        return self._tag.attrs["parentBiblId"]

    def get_parent_bibl_text(self) -> str:
        return self._gusev_tei_document.get_bibl_text_by_id(self.get_parent_bibl_id())

    def is_source_list_linking_candidate(self) -> bool:
        segment_text = self.get_text()

        if segment_text == "check":
            return False

        return GusevBiblTextSegment(segment_text).has_uncertain_type()
