from dataclasses import dataclass
import os
import re

import bs4
from tqdm import tqdm

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils
from tolstoy_bio.utilities.io import IoUtils


BIBLLIST_BIO_PATH = os.path.join(
    os.path.dirname(__file__), "../../../reference/bibllist_bio.xml"
)


REPORT_DUMP_PATH = os.path.join(
    os.path.dirname(__file__), "tolstoy-letter-openers-addressees-trimming-report.json"
)


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

    def get_title_main_text(self) -> str | None:
        title_main = self._get_title_main()
        return title_main.text.strip() if title_main else None

    def set_title_main_text(self, text: str) -> None:
        title_main = self._get_title_main() or self._create_title_main()
        title_main.string = text

    def _get_title_main(self) -> bs4.Tag | None:
        return self._soup.find("title", {"type": "main"})

    def _get_title_biodata(self) -> bs4.Tag | None:
        return BeautifulSoupUtils.find_if_single_or_fail(
            self._soup, "title", {"type": "biodata"}
        )

    def _create_title_main(self) -> bs4.Tag:
        title_main = bs4.BeautifulSoup("", "xml").new_tag(
            "title", attrs={"type": "main"}
        )

        self._get_title_biodata().insert_after(title_main)
        return title_main


class Item:
    def __init__(self, soup: bs4.Tag):
        self._soup = soup

    def get_id(self) -> str:
        return self._soup.find("ref", {"xml:id": True}).attrs["xml:id"].strip()

    def get_related_items(self) -> list[RelatedItem]:
        return [RelatedItem(element) for element in self._soup.find_all("relatedItem")]

    def set_title_main(self, text: str) -> None:
        title_main = self._get_title_main()
        title_main.string = text

    def _get_title_main(self) -> bs4.Tag:
        return BeautifulSoupUtils.find_if_single_or_fail(
            self._soup, "title", {"type": "main"}, recursive=False
        )


class BibllistBio:
    def __init__(self, path: str):
        soup = BeautifulSoupUtils.create_soup_from_file(path, "xml")
        self._soup = soup
        self._path = path

    def _get_item_by_id(self, id_: str) -> Item:
        element = self._soup.find("ref", {"xml:id": id_}).parent
        return Item(element)

    def get_items(self) -> dict[str, Item]:
        table = {}

        for item_element in self._soup.find_all("item"):
            item = Item(item_element)
            table[item.get_id()] = item

        return table

    def get_tolstoy_diaries_item(self) -> Item:
        return self._get_item_by_id("Tolstoy_diaries")

    def get_tolstoy_letters_item(self) -> Item:
        return self._get_item_by_id("Tolstoy_letters")

    def get_tolstaya_letters_item(self) -> Item:
        return self._get_item_by_id("SAT_letters")

    def get_tolstaya_diaries_item(self) -> Item:
        return self._get_item_by_id("SAT_diaries")

    def get_tolstaya_journals_item(self) -> Item:
        return self._get_item_by_id("SAT_journals")

    def get_makovitski_item(self) -> Item:
        return self._get_item_by_id("Makovicky_diaries")

    def get_goldenweizer_item(self) -> Item:
        return self._get_item_by_id("Goldenveizer_diaries")

    def get_gusev_item(self) -> Item:
        return self._get_item_by_id("Gusev_letopis")

    def save(self) -> None:
        content = self._soup.prettify()
        IoUtils.save_textual_data(content, self._path)


@dataclass
class SourceTitles:
    item: str
    related_item: str | None


titles_by_source_key: dict[str, SourceTitles] = {
    "Tolstoy_diaries": SourceTitles(
        item="Толстой Л. Н. Дневники",
        related_item="Л. Н. Толстой. Дневник",
    ),
    "Tolstoy_letters": SourceTitles(item="Толстой Л. Н. Письма", related_item=None),
    "SAT_letters": SourceTitles(
        item="Толстая С. А. Письма к Л. Н. Толстому",
        related_item="С. А. Толстая. Письмо к Л. Н. Толстому",
    ),
    "SAT_diaries": SourceTitles(
        item="Толстая С. А. Дневники", related_item="С. А. Толстая. Дневник"
    ),
    "SAT_journals": SourceTitles(
        item="Толстая С. А. Ежедневники", related_item="С. А. Толстая. Ежедневник"
    ),
    "Makovicky_diaries": SourceTitles(
        item="Маковицкий Д. П. Яснополянские записки",
        related_item="Д. П. Маковицкий. Яснополянские записки",
    ),
    "Goldenveizer_diaries": SourceTitles(
        item="Гольденвейзер А. Б. Вблизи Толстого",
        related_item="А. Б. Гольденвейзер. Вблизи Толстого",
    ),
    "Gusev_letopis": SourceTitles(
        item="Гусев Н. Н. Летопись жизни творчества Л. Н. Толстого",
        related_item="Н. Н. Гусев. Летопись жизни творчества Л. Н. Толстого",
    ),
}


def main():
    print("Loading bibllist_bio.xml data...")

    bibllist = BibllistBio(BIBLLIST_BIO_PATH)

    update_fixed_title_mains(bibllist)
    update_related_item_title_mains_for_tolstoy_letters(bibllist)

    print("Saving bibllist_bio.xml...")

    bibllist.save()

    print("Done!")


def update_fixed_title_mains(bibllist: BibllistBio):
    items = bibllist.get_items()

    for key, item in tqdm(list(items.items()), "Adding fixed main titles"):
        titles = titles_by_source_key[key]
        item.set_title_main(titles.item)

        if not titles.related_item:
            continue

        for related_item in item.get_related_items():
            related_item.set_title_main_text(titles.related_item)


def update_related_item_title_mains_for_tolstoy_letters(
    bibllist: BibllistBio, *, with_report: bool = False
):
    item = bibllist.get_tolstoy_letters_item()
    related_items = list(item.get_related_items())

    transformations_history = []

    for related_item in tqdm(related_items, "Processing Tolstoy's letters"):
        transformations = []

        main_title = related_item.get_title_main_text()
        main_title = re.sub(r"^Л\. Н\. Толстой\. ", "", main_title)

        transformations.append(main_title)

        if match := re.fullmatch(r"(\w+)\s+(\w\.(\s\w\.)?)", main_title):
            surname, initials = match.group(1), match.group(2)

            if surname == "Письмо":
                continue

            main_title = f"{initials} {surname}"
            transformations.append(main_title)

        if re.match(r"\w\.|гр\.", main_title, re.I):
            main_title = f"Письмо {main_title}"
            transformations.append(main_title)

        main_title, count = re.subn(r"Гр\.", "гр.", main_title)

        if count > 0:
            transformations.append(main_title)

        main_title = f"Л. Н. Толстой. {main_title}"
        related_item.set_title_main_text(main_title)

        if len(transformations) > 1:
            transformations_history.append(transformations)

    if with_report and transformations_history:
        formatted_transformations = [
            "\n".join(transformations) for transformations in transformations_history
        ]

        formatted_history = "\n-----\n".join(formatted_transformations)

        print("Tolstoy's letter related item main title transformation history:\n")
        print(formatted_history)
        print(
            f"\n{len(transformations_history)} Tolstoy's letter related items updated."
        )


if __name__ == "__main__":
    main()
