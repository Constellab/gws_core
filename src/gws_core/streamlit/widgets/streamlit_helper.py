

class StreamlitHelper():

    CSS_PREFIX = 'st-key-'

    @classmethod
    def get_element_css_class(cls, key: str) -> str:
        return cls.CSS_PREFIX + key

    @classmethod
    def get_page_height(cls, additional_padding: int = 0) -> str:
        """Return the height of the page
        # 8*2px of main padding
        # 16px of main row wrap (of a column)

        :return: _description_
        :rtype: str
        """
        return f"calc(100vh - {32 + additional_padding}px)"
