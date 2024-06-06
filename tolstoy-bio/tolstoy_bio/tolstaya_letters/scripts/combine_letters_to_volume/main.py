import os
from .volume_builder import create_volume


def main():
    module_folder_path = os.path.dirname(os.path.abspath(__file__))
    entries_repository_path = os.path.join(module_folder_path, "../../data/xml")
    target_repository_path = os.path.join(module_folder_path, "../../data")

    create_volume(entries_repository_path, target_repository_path)


if __name__ == "__main__":
    main()