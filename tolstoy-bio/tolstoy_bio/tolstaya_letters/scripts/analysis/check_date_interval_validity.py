import os

from tqdm import tqdm
from tolstoy_bio.utilities.io import IoUtils


def main():
    analyze()


def analyze():
    source_documents_repository_local_path = f'../../../data/xml'
    source_documents_repository_package_path = os.path.join(__file__, source_documents_repository_local_path)
    source_documents_repository_absolute_path = os.path.abspath(source_documents_repository_package_path)
    folder_paths = IoUtils.get_folder_contents_paths(source_documents_repository_absolute_path, ignore_hidden=True)

    invalid_names = []

    for folder_path in tqdm(folder_paths):
        files_names = IoUtils.get_folder_contents_names(folder_path, ignore_hidden=True)
        processed_names = [name.replace('.xml.xml', '') for name in files_names]

        for name in processed_names:
            _, start_date, end_date = name.split('_')

            if end_date < start_date:
                invalid_names.append(name)
        
    if invalid_names:
        print('The following names have invalid date interval:')
        print('\n'.join(invalid_names))
    else:
        print('All date intervals are valid.')


if __name__ == '__main__':
    main()
