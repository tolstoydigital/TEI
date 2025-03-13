import pandas as pd
from tqdm import tqdm

from tolstoy_bio.bibllist_bio.creating_source_list.source import Source


class SourceProvider:
    @staticmethod
    def read_sources_from_excel_table(
        excel_table_path: str, sheet_name: str | None = None
    ) -> list[Source]:
        table = pd.read_excel(excel_table_path, sheet_name=sheet_name, dtype=str)

        table.fillna("", inplace=True)

        return [
            Source(
                index=entry["Unnamed: 0"],
                main_title=entry["title_main"],
                bibliographic_title=entry["title_bibl"],
                author=entry["автор"],
                editor=entry["редактор"],
                work=entry["заголовок работы"],
                anthology=entry["опубликова в"],
                publisher=entry["издатнльство "],
                volume=entry["том, книга, выпуск"],
                publication_place=entry["место издания"],
                publication_date=entry["дата издания"],
                storage=entry["место хранения"],
            )
            for _, entry in tqdm(
                table.iterrows(), "Parsing sources from XLSX table", len(table)
            )
        ]
