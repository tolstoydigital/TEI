from dataclasses import dataclass


@dataclass
class VolumeBuildingConfig:
    volume_id: str  
    subvolumes_ids: list[str]
    title: str
    main_title: str
    bibl_title: str
    from_date: str
    to_date: str
    editor_date: str


def get_volumes_configs():
    return [
        VolumeBuildingConfig(
            volume_id="makovitski-diaries_1904_1905",
            subvolumes_ids=[
                "makovitski-diaries_1904_1904",
                "makovitski-diaries_1905_1905",
            ],
            title="Д. П. Маковицкий. Яснополянские записки. 1904–1905",
            main_title="Д. П. Маковицкий. Яснополянские записки. 1904–1905",
            bibl_title="Маковицкий Д. П. У Толстого, 1904—1910: «Яснополянские записки»: В 5 кн. / АН СССР. Ин-т мировой лит. им. А. М. Горького. — М.: Наука, 1979—1981. — (Лит. наследство; Т. 90). Кн. 1: 1904—1905. — 1979.",
            from_date="1904-10-26",
            to_date="1905-12-31",
            editor_date="26 октября 1904 — 31 декабря 1905"
        ),

        VolumeBuildingConfig(
            volume_id="makovitski-diaries_1906_1907",
            subvolumes_ids=[
                "makovitski-diaries_1906_1906",
                "makovitski-diaries_1907_1907",
            ],
            title="Д. П. Маковицкий. Яснополянские записки. 1906–1907",
            main_title="Д. П. Маковицкий. Яснополянские записки. 1906–1907",
            bibl_title="Маковицкий Д. П. У Толстого, 1904—1910: «Яснополянские записки»: В 5 кн. / АН СССР. Ин-т мировой лит. им. А. М. Горького. — М.: Наука, 1979—1981. — (Лит. наследство; Т. 90). Кн. 2: 1906—1907. — 1979.",
            from_date="1906-01-01",
            to_date="1907-12-31",
            editor_date="1 января 1906 — 31 декабря 1907"
        ),

        VolumeBuildingConfig(
            volume_id="makovitski-diaries_1908_1909",
            subvolumes_ids=[
                "makovitski-diaries_1908_1908",
                "makovitski-diaries_1909-01_1909-06",
            ],
            title="Д. П. Маковицкий. Яснополянские записки. 1908–1909",
            main_title="Д. П. Маковицкий. Яснополянские записки. 1908–1909",
            bibl_title="Маковицкий Д. П. У Толстого, 1904—1910: «Яснополянские записки»: В 5 кн. / АН СССР. Ин-т мировой лит. им. А. М. Горького. — М.: Наука, 1979—1981. — (Лит. наследство; Т. 90). Кн. 3: 1908—1909 (январь — июнь). — 1979.",
            from_date="1908-01-01",
            to_date="1909-06-30",
            editor_date="1 января 1908 — 30 июня 1909"
        ),

        VolumeBuildingConfig(
            volume_id="makovitski-diaries_1909_1910",
            subvolumes_ids=[
                "makovitski-diaries_1909-07_1909-12",
                "makovitski-diaries_1910_1910",
            ],
            title="Д. П. Маковицкий. Яснополянские записки. 1909–1910",
            main_title="Д. П. Маковицкий. Яснополянские записки. 1909–1910",
            bibl_title="Маковицкий Д. П. У Толстого, 1904—1910: «Яснополянские записки»: В 5 кн. / АН СССР. Ин-т мировой лит. им. А. М. Горького. — М.: Наука, 1979—1981. — (Лит. наследство; Т. 90). Кн. 4: 1909 (июль — декабрь) — 1910. — 1979.",
            from_date="1909-07-01",
            to_date="1910-11-07",
            editor_date="1 июля 1909 — 7 ноября 1910"
        )
    ]