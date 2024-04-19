from xmltodict import parse, unparse


class XMLHelper:

    @staticmethod
    def xml_to_dict(xml_text: str) -> dict:
        return parse(xml_text)

    @staticmethod
    def dict_to_xml(dict_: dict) -> str:
        return unparse(dict_)
