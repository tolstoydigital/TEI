import os
from tolstoy_bio.makovitski.scripts.convert_to_xml.converter import FebHtmlToTeiXmlConverter
from tolstoy_bio.utilities.io import IoUtils


def main():
    years = ['1904', '1905', '1906', '1907', '1908', '1909-till-june', '1909-from-july', '1910']

    for year in years:
        print(f'Processing doc {year}...')

        reading_path = os.path.abspath(os.path.join(__file__, f'../../../data/source_html/normalized/{year}.html'))
        saving_path = os.path.abspath(os.path.join(__file__, f'../../../data/xml/by_year/{year}.xml'))

        document = FebHtmlToTeiXmlConverter.from_path(reading_path)
        document.convert_to_tei()
        document.save_to_file(saving_path)


if __name__ == '__main__':
    main()