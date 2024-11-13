from dataclasses import dataclass
import os
import sys

import bs4
import pandas as pd
from tqdm import tqdm

from tolstoy_bio.utilities.beautiful_soup import BeautifulSoupUtils


LOCATION_LIST_XML_TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__), "location-list-template.xml"
)

LOCATION_LIST_XML_PATH = os.path.join(
    os.path.dirname(__file__), "../../../../reference/locationList.xml"
)

BIBLLIST_BIO_PATH = os.path.join(
    os.path.dirname(__file__), "../../../../reference/bibllist_bio.xml"
)

LINKAGE_MAP_PATH = os.path.join(os.path.dirname(__file__), "linkage-map.csv")


def parse_location_table_path_from_arguments() -> None:
    arguments = sys.argv[1:]

    if not arguments:
        raise ValueError(
            "Path to the source XLSX table expected as the first argument."
        )

    return arguments[0]


@dataclass
class Location:
    id: str
    label: str
    latitude: str
    longitude: str


def parse_locations_from_xlsx_table(table_path: str) -> list[Location]:
    table = pd.read_excel(table_path, dtype=str)

    locations: list[Location] = []

    for _, entry in tqdm(
        table.iterrows(), "Parsing locations from XLSX table", len(table)
    ):
        locations.append(
            Location(
                id=entry["id"],
                label=entry["Название локации"],
                latitude=entry["Широта"],
                longitude=entry["Долгота"],
            )
        )

    return locations


def create_xml_list_from_locations(
    locations: list[Location], *, template_path: str, output_path: str
) -> None:
    template_soup: bs4.BeautifulSoup = BeautifulSoupUtils.create_soup_from_file(
        template_path, "xml"
    )

    place_list = BeautifulSoupUtils.find_if_single_or_fail(template_soup, "listPlace")

    for location in tqdm(locations, "Creating locationList.xml"):
        place = template_soup.new_tag("place", attrs={"xml:id": location.id})

        place_name = template_soup.new_tag("placeName")
        place_name.string = location.label
        place.append(place_name)

        geo = template_soup.new_tag("geo")
        geo.string = f"{location.latitude} {location.longitude}"
        place.append(geo)

        place_list.append(place)

    template_soup.smooth()
    BeautifulSoupUtils.prettify_and_save(template_soup, output_path)


@dataclass
class LocationDetectionRule:
    location_id: str
    trigger_substrings: list[str]


def parse_location_detection_rules(map_csv_path: str) -> list[LocationDetectionRule]:
    table = pd.read_csv(
        map_csv_path, delimiter=";", names=["substring", "count", "location_id"]
    )

    entries_by_location_id = table.groupby(["location_id"])

    rules: list[LocationDetectionRule] = []

    for (location_id,), entries in entries_by_location_id:
        trigger_substrings = [entry["substring"] for _, entry in entries.iterrows()]
        rules.append(LocationDetectionRule(location_id, trigger_substrings))

    return rules


def add_locations_to_bibllist_bio(
    *,
    location_detection_rules: list[LocationDetectionRule],
    bibllist_bio_path: str,
) -> None:
    print("Loading bibllist_bio.xml...")

    bibllist_bio_soup = BeautifulSoupUtils.create_soup_from_file(
        bibllist_bio_path, "xml"
    )

    related_items = list(bibllist_bio_soup.find_all("relatedItem"))

    for related_item in tqdm(related_items, "Adding locations to related items"):
        opener = BeautifulSoupUtils.find_if_single_or_fail(related_item, "opener")
        opener_text = opener.text.strip()

        applicable_location_ids = [
            rule.location_id
            for rule in location_detection_rules
            if any(
                trigger_substring.lower() in opener_text.lower()
                for trigger_substring in rule.trigger_substrings
            )
        ]

        if not applicable_location_ids:
            continue

        if len(applicable_location_ids) > 1:
            # TODO: decide how to handle such cases
            continue

        applicable_location_id = applicable_location_ids[0]

        location_relation = BeautifulSoupUtils.find_if_single_or_fail(
            related_item, "relation", attrs={"type": "location"}
        )

        assert location_relation.attrs["ref"] == "EMPTY"

        location_relation.attrs["ref"] = applicable_location_id

    print("Saving bibllist_bio.xml...")
    
    BeautifulSoupUtils.prettify_and_save(bibllist_bio_soup, bibllist_bio_path)


def main():
    location_table_path = parse_location_table_path_from_arguments()
    locations = parse_locations_from_xlsx_table(location_table_path)

    create_xml_list_from_locations(
        locations,
        template_path=LOCATION_LIST_XML_TEMPLATE_PATH,
        output_path=LOCATION_LIST_XML_PATH,
    )

    location_detection_rules = parse_location_detection_rules(LINKAGE_MAP_PATH)

    add_locations_to_bibllist_bio(
        location_detection_rules=location_detection_rules,
        bibllist_bio_path=BIBLLIST_BIO_PATH,
    )

    print("Done!")


if __name__ == "__main__":
    main()
