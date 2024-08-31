import os
from tqdm import tqdm

from tolstoy_bio.utilities.io import IoUtils
from .fragment_processor import FragmentProcessor
from .record_id_manager import RecordIdManager


SOURCE_REPOSITORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../data/source")
TEI_REPOSITORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../data/tei")


def main():
    fragments_paths = IoUtils.get_folder_contents_paths(SOURCE_REPOSITORY, ignore_hidden=True)
    record_id_manager = RecordIdManager()

    for fragment_path in tqdm(sorted(fragments_paths)):
        try:
            fragment_processor = FragmentProcessor(fragment_path, record_id_manager)
            fragment_processor.convert_records_to_tei(TEI_REPOSITORY)
        except Exception as e:
            print(fragment_path)
            raise e


if __name__ == "__main__":
    main()
