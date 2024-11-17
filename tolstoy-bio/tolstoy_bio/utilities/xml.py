import re
from uuid import uuid4

from lxml import etree


class XmlUtils:

    @staticmethod
    def validate_xml_or_fail(
        content: str, *, should_recover: bool = False, ignore_xml_ids: bool = False
    ) -> None:
        if ignore_xml_ids:
            content = re.sub(r'xml:id=".*?"', lambda _: f'xml:id="id-{uuid4()}"', content)

        parser = etree.XMLParser(recover=True) if should_recover else None
        etree.fromstring(content.encode(), parser)
