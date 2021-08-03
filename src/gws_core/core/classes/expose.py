# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

class Expose:

    @classmethod
    def analyze(cls, module) -> dict:
        data = {
            "doc": module.doc(),
            "name": module.name(),
            "tree": module.tree()
        }
        cls.__parse_node(data["tree"])
        return data

    @classmethod
    def __parse_node(cls, node: dict) -> dict:
        from ..model.model import Model
        for k in node:
            is_node = k.startswith(":")
            if is_node:
                val = node[k]
                t: Model = val.get("type")
                if t and issubclass(t, Model):
                    val["type"] = t.full_classname()

                cls.__parse_node(val)
