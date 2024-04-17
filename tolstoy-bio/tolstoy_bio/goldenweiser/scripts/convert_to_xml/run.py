import os
from tolstoy_bio.goldenweiser.scripts.convert_to_xml.converter import GoldenweiserIntermediateMarkupGenerator
from tolstoy_bio.goldenweiser.scripts.utils import generate_name
from tolstoy_bio.utilities.io import IoUtils


def main():
    process()


def process():
    processor = GoldenweiserIntermediateMarkupGenerator()
    processor.convert_to_xml()
    result = processor.xml_soup_to_string()
    IoUtils.save_textual_data(result, get_saving_path())


def get_saving_path():
    name = generate_name('1896', '1910').to_filename('xml')
    return os.path.abspath(os.path.join(__file__, f'../../../data/xml/{name}'))



if __name__ == "__main__":
    main()