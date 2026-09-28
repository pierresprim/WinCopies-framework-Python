from types import NotImplementedType
from typing import cast

def ThrowIfNotImplemented[T](value: T|NotImplementedType) -> T:
    if value is NotImplemented: raise NotImplementedError()

    return cast(T, value)