from lxml import etree


class XmlUtils:

    @staticmethod
    def validate_xml_or_fail(content: str, *, should_recover: bool = False) -> None:
        parser = etree.XMLParser(recover=True) if should_recover else None
        etree.fromstring(content.encode(), parser)
