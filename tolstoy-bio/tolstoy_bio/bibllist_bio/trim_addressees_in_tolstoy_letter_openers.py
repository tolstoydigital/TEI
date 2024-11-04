import os
import re

import bs4
from tqdm import tqdm

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils
from tolstoy_bio.utilities.io import IoUtils


BIBLLIST_BIO_PATH = os.path.join(
    os.path.dirname(__file__), "../../../reference/bibllist_bio.xml"
)


REPORT_DUMP_PATH = os.path.join(os.path.dirname(__file__), "report.json")


EXCEPTIONAL_OPENER_TEXT_UPDATES = {
    "П. В. Веригину .24 июня.": "24 июня.",
    "Приставу 2-го стана Крапивенского уезда.1864 г. Март. Я. П.": "1864 г. Март. Я. П.",
    "Н. Н. Страхову.": "",
    "Мировому посреднику 1-го участка Крапивенского уезда В. Долинино-Ивановскому.1870 г. Февраля 8. Я. П.": "1870 г. Февраля 8. Я. П.",
    "Тульскому губернатору.1 Губернскому присутствию. Генерал-майору графу Ламберту .21861 г. Июля середина. Я. П.": "1861 г. Июля середина. Я. П.",
    "Циркулярный ответ авторам, присылающим свои рукописи. 1 См. прим. к письму № 62. 1909 г. Июня 1. Я. П.": "1909 г. Июня 1. Я. П.",
    "З1. М. П. Скипетрову. Неотправленное.1909 г. Июля 14. Я. П.": "1909 г. Июля 14. Я. П.",
    "В Московский международный банк в Туле. Льва Николаевича Толстого": "",
    "Редакции «Neuen Gesellschaftlichen Correspondent».Октября12/25. Я. П.": "Октября12/25. Я. П.",
    "И. Каменову (I. Kamenov) .": "",
    "Мировому посреднику 2 участка Крапивенского уезда А. Н. Костомарову .1870 г. Ноября 8…10. Я. П.": "1870 г. Ноября 8…10. Я. П.",
    "В. В. Битнеру.(С. -Петербург, Невский, 40)": "(С. -Петербург, Невский, 40)",
    "Приставу 2 стана Крапивенского уезда.1861 г. Ноября 10. Я. П.": "1861 г. Ноября 10. Я. П.",
    "Судебному следователю 19 участка г. Петербурга.1909 г. Февраля 27. Я. П.": "1909 г. Февраля 27. Я. П.",
    "В газету. 1 Слова: В газету воспроизводятся по черновику-автографу. Неотправленное.1910 г. Марта 15. Я. П.": "1910 г. Марта 15. Я. П.",
    "П. И. Бирюкову .": "",
    "А. Н. Пыпину .": "",
    "Записка к завещанию от 1 ноября 1909 г. 1909 г. Октября 31? — ноября 1? Я. П.": "1909 г. Октября 31? — ноября 1? Я. П.",
    "T. A. Берс.[РукойС. А. Толстой]21-гомарта 1863.Чтоты, Танька , приуныла... — Совсем мне не пишешь, а я так люблю получать твои письма, и Левочке ответа еще нет на его сумасбродное послание. Я в нем ровно ничего не поняла.1863г. Марта 23. Я. П.": "[РукойС. А. Толстой]21-гомарта 1863.Чтоты, Танька , приуныла... — Совсем мне не пишешь, а я так люблю получать твои письма, и Левочке ответа еще нет на его сумасбродное послание. Я в нем ровно ничего не поняла.1863г. Марта 23. Я. П.",
    "Е. А. Лёве (Eugen von Loewe) . 1 См. прим. 1 к письму № 13. В 1890 г. в Германии было напечатано несколько переводов «Крейцеровой сонаты» (Р. Лёвенфельда, Гауфа и Роскошного). 1890 г. Июня 30. Я. П.": "См. прим. 1 к письму № 13. В 1890 г. в Германии было напечатано несколько переводов «Крейцеровой сонаты» (Р. Лёвенфельда, Гауфа и Роскошного). 1890 г. Июня 30. Я. П.",
    "Тульскому губернатору. 1 Губернатором был П. М. Дараган. 1861 г. Октября 28. Я. П.": "Губернатором был П. М. Дараган. 1861 г. Октября 28. Я. П.",
}


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

    def get_related_items(self) -> list[RelatedItem]:
        return [RelatedItem(element) for element in self._soup.find_all("relatedItem")]


class Bibllist:
    def __init__(self, path: str):
        soup = BeautifulSoupUtils.create_soup_from_file(path, "xml")
        self._soup = soup
        self._path = path

    def _get_item_by_id(self, id_: str) -> Item:
        element = self._soup.find("ref", {"xml:id": id_}).parent
        return Item(element)

    def get_tolstoy_letters_item(self) -> Item:
        return self._get_item_by_id("Tolstoy_letters")

    def save(self) -> None:
        content = self._soup.prettify()
        IoUtils.save_textual_data(content, self._path)


def main():
    print("Loading bibllist_bio.xml data...")

    bibllist = Bibllist(BIBLLIST_BIO_PATH)

    print("Collecting related items...")

    item = bibllist.get_tolstoy_letters_item()
    related_items = item.get_related_items()

    related_items_by_document_id = {
        related_item.get_document_id(): related_item
        for related_item in tqdm(related_items, "Hashing related items")
    }

    original_opener_texts_by_document_id = {
        document_id: related_item.get_opener_text()
        for document_id, related_item in tqdm(
            related_items_by_document_id.items(),
            "Collecting original opener texts",
            len(related_items_by_document_id),
        )
    }

    updated_opener_texts_by_document_id = {
        document_id: trim_opener_text(opener_text)
        for document_id, opener_text in tqdm(
            original_opener_texts_by_document_id.items(),
            "Updating opener texts",
            len(original_opener_texts_by_document_id),
        )
    }

    for document_id, updated_opener_text in tqdm(
        updated_opener_texts_by_document_id.items(),
        "Setting opener texts",
        len(updated_opener_texts_by_document_id),
    ):
        related_item = related_items_by_document_id[document_id]
        related_item.set_opener_text(updated_opener_text)

    print("Saving bibllist_bio.xml...")

    bibllist.save()

    print("bibllist_bio.xml has been saved successfully.")

    report = []

    for document_id in tqdm(
        related_items_by_document_id.keys(),
        "Generating report",
        len(related_items_by_document_id),
    ):
        report.append(
            {
                "id": document_id,
                "old": original_opener_texts_by_document_id[document_id],
                "new": updated_opener_texts_by_document_id[document_id],
            }
        )

    print("Saving the report...")

    IoUtils.save_as_json(report, REPORT_DUMP_PATH, indent=2)

    print("Done!")


def trim_opener_text(opener_text: str) -> str:
    return trim_addressee(trim_ordinal_number(opener_text))


def trim_ordinal_number(opener_text: str) -> str:
    return re.sub(r"^\d+[aа]", "", opener_text).lstrip(". ")


def trim_addressee(opener_text: str) -> str:
    if not opener_text:
        return ""

    if not re.match(r"\D*\d{4}", opener_text):
        return EXCEPTIONAL_OPENER_TEXT_UPDATES[opener_text]

    return re.sub(r"^\D*(\d{4})", r"\1", opener_text)


if __name__ == "__main__":
    main()
