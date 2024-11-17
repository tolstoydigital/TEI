import re

import bs4

from .tei_note import TeiNote


def replace_square_brackets_with_cursive(footnote: TeiNote) -> None:
    note_soup = footnote.get_note_soup()
    note_xml = str(note_soup)
    updated_note_xml = re.sub(r"\[(.*?)\](?![^<]*>)", r'<hi rend="italic">\1</hi>', note_xml)
    updated_note_soup_container = bs4.BeautifulSoup(updated_note_xml, "xml")
    updated_note_soup = updated_note_soup_container.find("note")
    note_soup.replace_with(updated_note_soup)
