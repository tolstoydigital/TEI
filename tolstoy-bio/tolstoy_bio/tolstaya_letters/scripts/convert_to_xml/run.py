import os

import bs4
from tqdm import tqdm
from tolstoy_bio.tolstaya_letters.scripts.convert_to_xml.converter import TolstayaLetterFebHtmlToTeiXmlConverter
from tolstoy_bio.utilities.io import IoUtils


def main():
    process_documents()


def process_documents():
    source_documents_repository_local_path = f'../../../data/source_html/normalized'
    source_documents_repository_package_path = os.path.join(__file__, source_documents_repository_local_path)
    source_documents_repository_absolute_path = os.path.abspath(source_documents_repository_package_path)

    folder_names = IoUtils.get_folder_contents_names(source_documents_repository_absolute_path, ignore_hidden=True)
    folder_paths = IoUtils.get_folder_contents_paths(source_documents_repository_absolute_path, ignore_hidden=True)

    saved_filenames = set()

    for folder_name, folder_path in tqdm(zip(folder_names, folder_paths), total=len(folder_paths)):
        print(f'Processing folder {folder_name}...')

        files_names = IoUtils.get_folder_contents_names(folder_path, ignore_hidden=True)
        files_paths = IoUtils.get_folder_contents_paths(folder_path, ignore_hidden=True)

        for source_file_name, file_path in zip(files_names, files_paths):
            print(f'Processing file {source_file_name}...')

            document = TolstayaLetterFebHtmlToTeiXmlConverter.from_path(file_path)
            document.convert_to_tei()

            target_file_name = document.get_document_id()
            assert target_file_name not in saved_filenames, f'The XML document with filename "{target_file_name}" has already been created before'

            saving_path = os.path.abspath(os.path.join(__file__, f'../../../data/xml/{target_file_name}.xml'))
            document.save_to_file(saving_path)

            saved_filenames.add(target_file_name)


if __name__ == '__main__':
    main()