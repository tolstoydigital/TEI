from dataclasses import dataclass

import bs4

from .gusev_bibl_text import GusevBiblText


@dataclass
class GusevBiblElement:
    element: bs4.Tag

    def get_text(self) -> GusevBiblText:
        return GusevBiblText(text=self.element.text.strip())