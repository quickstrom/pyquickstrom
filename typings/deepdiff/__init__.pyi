from typing import Dict, Iterable, Tuple, TypedDict

DiffPath = str

class ValueChangedDiff(TypedDict):
    old_value: object
    new_value: object

class DiffDict(TypedDict):
    values_changed: Dict[DiffPath, ValueChangedDiff]
    iterable_item_added: Dict[DiffPath, object]
    iterable_item_removed: Dict[DiffPath, object]

DeepDiff = DiffDict
