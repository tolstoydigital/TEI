from argparse import ArgumentParser
import os

from tolstoy_bio.bibllist_bio.creating_source_list.source_provider import SourceProvider
from tolstoy_bio.bibllist_bio.creating_source_list.source_id_generator import (
    SourceIdGenerator,
)
from tolstoy_bio.bibllist_bio.creating_source_list.source_xml_entity_builder import (
    XmlSourceListBuilder,
)


SOURCE_LIST_XML_PATH = os.path.join(
    os.path.dirname(__file__), "../../../../reference/sourceList.xml"
)


def main():
    print("Parsing arguments...")

    cli = ArgumentParser()
    cli.add_argument("-t", "--table", type=str, default=None)
    cli.add_argument("-s", "--sheet", type=str, default=None)

    arguments = cli.parse_args()

    excel_table_path = arguments.table
    excel_table_sheet_name = arguments.sheet

    if not excel_table_path:
        raise ValueError("Table path is required in system arguments.")

    print(f"Parsing excel table from path {excel_table_path}...")

    sources = SourceProvider.read_sources_from_excel_table(
        excel_table_path, excel_table_sheet_name
    )

    source_id_generator = SourceIdGenerator()

    for source in sources:
        source.set_id(source_id_generator.generate(source))

    # print("\n".join([source.id for source in sources]))

    assert all(source.id[0].isalpha() for source in sources), [
        source.id for source in sources if not source.id[0].isalpha()
    ]

    xml_builder = XmlSourceListBuilder(sources)

    xml_builder.build_soup()
    xml_builder.save_as_xml(SOURCE_LIST_XML_PATH)


if __name__ == "__main__":
    main()
