
from typing import Dict

from .kv_store import KVStore


class ResourceSerialized():
    """Serialized resource. Used to save the resource data


    Attributes:
        light_data  Small data of the resource store in the database. This dictionnary must not be to big/
                    Information in the light data will be searchable  with a full text search


        data        To store big data. This will be store in a file on the server. It will not be searchable
    """

    light_data: Dict

    kv_store: KVStore

    def __init__(self, light_data: Dict = None, kv_store: KVStore = None) -> None:
        self.light_data = light_data
        self.kv_store = kv_store

    def has_light_data(self) -> bool:
        return self.light_data is not None and len(self.light_data) > 0

    def has_kv_store(self) -> bool:
        return self.kv_store is not None and isinstance(self.kv_store, KVStore)
