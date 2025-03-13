import re

import bs4

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils


def get_processed_entry_div(entry_document_path: str):
    soup = BeautifulSoupUtils.create_soup_from_file(entry_document_path, "xml")
    entry_id = get_entry_id(soup)

    soup = extract_body(soup)
    remove_classes(soup)
    unwrap_text_division(soup)
    soup = preprocess_openers(soup)
    fix_notes(soup)
    remove_empty_paragraphs(soup)
    make_ids_global(soup, entry_id)

    body = soup.find("body") if soup.name != "body" else soup
    body.name = "div"
    body.attrs = { "type": "letter" }

    return body


def get_entry_id(soup: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
    return soup.find("title", attrs={"xml:id": True}).attrs["xml:id"].strip()


def extract_body(soup: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
    bodies = soup.find_all("body")

    assert len(bodies) == 1, "Unexpected number of bodies encountered"
    
    return bodies[0]


def remove_classes(soup: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
    for element in soup.find_all():
        if "class" in element.attrs:
            del element.attrs["class"]


def unwrap_text_division(soup: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
    divisions = soup.find_all("div", attrs={
        "type": "text",
    })

    assert len(divisions) == 1, "Unexpected number of target divisions encountered"

    division = divisions[0]
    division.unwrap()


def preprocess_openers(soup: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
    openers = soup.find_all("opener")

    for opener in openers:
        opener = openers[0]

        move_date_to_opener(opener)
        unwrap_datelines(opener)
        unwrap_dates(opener)
        prepare_substrings_in_square_brackets(opener)

    return process_substrings_in_square_brackets(soup)


def move_date_to_opener(opener: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
    date = opener.find("date")

    if date:
        opener.attrs.update(date.attrs)


def unwrap_datelines(soup: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
    datelines = soup.find_all("dateline")

    for dateline in datelines:
        dateline.unwrap()


def unwrap_dates(soup: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
    dates = soup.find_all("date")

    for date in dates:
        date.unwrap()


def prepare_substrings_in_square_brackets(soup: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
    START = r"%START_ADD%"
    END = r"%END_ADD%"

    texts = soup.find_all(string=True)

    for text in texts:
        text.string.replace_with(
            re.sub(r"\[(.*?)\]", rf'{START}\1{END}', text.string)
        )


def process_substrings_in_square_brackets(soup: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
    START = r"%START_ADD%"
    END = r"%END_ADD%"

    stringified_soup = soup.prettify()
    
    stringified_soup = stringified_soup.replace(START, '<add resp="volume_editor">')
    stringified_soup = stringified_soup.replace(END, "</add>")
    return bs4.BeautifulSoup(stringified_soup, "xml")


def fix_notes(soup: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
    loose_notes = soup.find_all("note", attrs={
        "xml:id": False
    })

    refs = soup.find_all("ref")
    refs_without_following_note = []

    for ref in refs:
        if not ref.next_sibling:
            refs_without_following_note.append(ref)
        
        if not ref.next_sibling.name == "note":
            refs_without_following_note.append(ref)

    for i, note in enumerate(loose_notes, 1):
        hi = note.find("hi")

        if not hi:
            continue

        hi_text = hi.text.strip()

        matching_ref = next((ref for ref in refs if ref.text.strip() == hi_text), None)

        if not matching_ref:
            continue

        matching_ref.insert_after(note)
        matching_ref.attrs["target"] = f"#fixed-note-{i}"
        note.attrs["xml:id"] = f"fixed-note-{i}"
        del note.attrs["type"]


def remove_empty_paragraphs(soup: bs4.BeautifulSoup) -> bs4.BeautifulSoup:
    for p in soup.find_all("p"):
        if p.text.strip() == "":
            p.decompose()


def make_ids_global(soup: bs4.BeautifulSoup, prefix: str) -> bs4.BeautifulSoup:
    xml_id_elements = soup.find_all(attrs={"xml:id": True})

    for element in xml_id_elements:
        element.attrs["xml:id"] = prefix + "__" + element.attrs["xml:id"]

    assert len(xml_id_elements) == len(set([e.attrs["xml:id"] for e in xml_id_elements])), "!"

    refs = soup.find_all("ref", attrs={"target": True})

    for element in refs:
        if element.attrs["target"].startswith("#"):
            element.attrs["target"] = "#" + prefix + "__" + element.attrs["target"].strip("#")
        else:
            element.attrs["target"] = prefix + "__" + element.attrs["target"]
    
    assert len(refs) == len(set([e.attrs["target"] for e in refs])), "!"