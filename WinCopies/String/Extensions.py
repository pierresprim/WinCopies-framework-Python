from collections.abc import Iterable

from WinCopies.Collections import Iteration
from WinCopies.String import Join
from WinCopies.Typing.Delegate import Selector

def BuildFrom(values: Iterable[str], selector: Selector[str]) -> str:
    return Join(Iteration.Select(values, selector))
def BuildFromValues(*values: str, selector: Selector[str]) -> str:
    return BuildFrom(values, selector)

def ConcatenateFrom(values: Iterable[str], separator: str, selector: Selector[str]) -> str:
    return separator.join(Iteration.Select(values, selector))
def ConcatenateFromValues(separator: str, selector: Selector[str], *values: str) -> str:
    return ConcatenateFrom(values, separator, selector)