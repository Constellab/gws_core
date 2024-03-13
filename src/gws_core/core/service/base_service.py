

class BaseService:
    _number_of_items_per_page = 20

    @classmethod
    def get_number_of_item_per_page(cls, number_of_items_per_page: int = 20):
        return min(number_of_items_per_page, cls._number_of_items_per_page)
