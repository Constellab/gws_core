

class StreamlitHelper():

    CSS_PREFIX = 'st-key-'

    @classmethod
    def get_element_css_class(cls, key: str):
        return cls.CSS_PREFIX + key
