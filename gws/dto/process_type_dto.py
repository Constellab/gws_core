

from typing import Dict, List, Optional


class ProcessTypeTree():
    """
    Class used to regroup the process type by ptype modules
    """

    ptype_part: str

    # If this is a branch, contains the list of sub modules
    sub_modules: Optional[List['ProcessTypeTree']] = None

    # if this is a leaf, contain the process type
    process_type: Optional[Dict] = None

    def __init__(self, ptype_part: str, process_type: Optional[Dict] = None):
        self.ptype_part = ptype_part

        if process_type is not None:
            self.process_type = process_type
        else:
            self.sub_modules = []

    def add_process_type(self, types: List[str], process_type: Dict):

        # if we reach the class name of the type
        if len(types) == 1:
            process_ordered: 'ProcessTypeTree' = ProcessTypeTree(
                types[0], process_type)
            self.sub_modules.append(process_ordered)
        else:
            # add proces recursively
            sub_module: ProcessTypeTree = self.get_submodule_with_type(
                types[0])
            if sub_module is None:
                sub_module = ProcessTypeTree(types[0])
                self.sub_modules.append(sub_module)

            sub_module.add_process_type(types[1::], process_type)

    def get_submodule_with_type(self, ptype_part: str) -> Optional['ProcessTypeTree']:
        for sub_module in self.sub_modules:
            if sub_module.ptype_part == ptype_part:
                return sub_module

        return None
