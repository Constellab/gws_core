from typing import Dict, List, Optional


class TypedTree():
    """
    Class used to create a tree of object by python type
    """

    type_part: str

    # If this is a branch, contains the list of sub modules
    sub_trees: Optional[List['TypedTree']] = None

    # if this is a leaf, contain the process type
    object: Optional[Dict] = None

    def __init__(self, type_part: str, obj: Optional[Dict] = None):
        self.type_part = type_part

        if obj is not None:
            self.object = obj
        else:
            self.sub_trees = []

    def add_object(self, types: List[str], obj: Dict):
        """
        Add an object to the tree to existing sub tree or create an new sub tree if it exits
        """
        # if we reach the class name of the type
        if len(types) == 1:
            process_ordered: 'TypedTree' = TypedTree(
                types[0], obj)
            self.sub_trees.append(process_ordered)
        else:
            # add proces recursively
            sub_module: TypedTree = self._get_submodule_with_type_part(
                types[0])
            if sub_module is None:
                sub_module = TypedTree(types[0])
                self.sub_trees.append(sub_module)

            sub_module.add_object(types[1::], obj)

    # return the sub module with type part if it exists
    def _get_submodule_with_type_part(self, type_part: str) -> Optional['TypedTree']:
        for sub_module in self.sub_trees:
            if sub_module.type_part == type_part:
                return sub_module

        return None
