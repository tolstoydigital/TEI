from collections import defaultdict
from dataclasses import dataclass
import os

from tqdm import tqdm

from tolstoy_bio.utilities.io import IoUtils


GUSEV_TEI_REPOSITORY_PATH = os.path.join(os.path.dirname(__file__), "../../data/tei")


@dataclass
class GusevRecordMetadata:
    volume: int
    start_page: int
    end_page: int


def main():
    record_paths = IoUtils.get_folder_contents_paths(
        GUSEV_TEI_REPOSITORY_PATH, ignore_hidden=True
    )

    record_filenames = [os.path.basename(path) for path in record_paths]

    records_metadata = sorted(
        [parse_metadata_from_filename(filename) for filename in record_filenames],
        key=lambda metadata: (metadata.volume, metadata.start_page, metadata.end_page),
    )

    pages_by_volume: dict[str, list[int]] = defaultdict(list)

    for metadata in tqdm(records_metadata, "Collecting pages"):
        pages: list[int] = convert_range_bounds_to_numbers(
            metadata.start_page, metadata.end_page
        )

        pages_by_volume[metadata.volume].extend(pages)

    print(pages_by_volume)

    print("Finding missing pages...")

    missing_pages_by_volume: dict[str, list[int]] = {
        volume: get_missing_consecutive_numbers(pages)
        for volume, pages in pages_by_volume.items()
    }

    for volume, missing_pages in missing_pages_by_volume.items():
        print(f"Том {volume}")
        print(f"------------")
        print("\n".join([str(page) for page in missing_pages]))


def parse_metadata_from_filename(filename: str) -> GusevRecordMetadata:
    _, volume, start_page, end_page, *_ = filename.split("_")

    if filename == "gusev_v1_096_097_1855_08_27_1855_08_27.xml":
        start_page = "97"

    if filename == "gusev_v1_147_148_1857_02_26_1857_02_26.xml":
        start_page = "148"

    if filename == "gusev_v1_522_523_1880_03_16_1880_03_16.xml":
        start_page = "523"

    if filename == "gusev_v2_079_719_1909_10_14_1909_10_14.xml":
        start_page = "80"
        end_page = "80"

    if filename == "gusev_v2_172_772_1910_05_19_1910_05_19.xml":
        end_page = "172"

    if filename == "gusev_v2_560_561_1906_08_11_1906_08_11.xml":
        start_page = "561"

    if filename == "gusev_v2_605_695_1909_06_11_1909_06_11.xml":
        end_page = "605"

    if filename == "gusev_v2_736_738_1910_01_02_1910_01_02.xml":
        end_page = "736"

    return GusevRecordMetadata(
        volume=int(volume.replace("v", "")),
        start_page=int(start_page),
        end_page=int(end_page),
    )


def convert_range_bounds_to_numbers(start_number: int, end_number: int) -> list[int]:
    return [number for number in range(start_number, end_number + 1)]


def get_missing_consecutive_numbers(numbers: list[int]) -> list[int]:
    if not numbers:
        return []

    missing_numbers: list[int] = []

    for index in range(len(numbers) - 1):
        current_number: int = numbers[index]
        next_number: int = numbers[index + 1]

        assert (
            next_number >= current_number
        ), f"The next number {next_number} is smaller than the previous {current_number}"

        if next_number - current_number > 1:
            for number in range(current_number + 1, next_number):
                missing_numbers.append(number)

    return missing_numbers


if __name__ == "__main__":
    main()
