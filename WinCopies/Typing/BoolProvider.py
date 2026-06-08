from abc import abstractmethod
from typing import final

from WinCopies import IInterface

class IBoolProvider(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsBool(self) -> bool:
        ...

    @final
    def __bool__(self) -> bool: return self.AsBool()
    
    @final
    def __nonzero__(self) -> bool: return self.AsBool()
class IAsBool[T](IBoolProvider):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def Not(self) -> T:
        ...

class INullableBoolProvider(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsNullableBool(self) -> bool|None:
        ...

def AsBool(value: IBoolProvider|None) -> bool:
    return False if value is None else value.AsBool()
def AsNullableBool(value: IBoolProvider|INullableBoolProvider|None) -> bool|None:
    return None if value is None else (value.AsBool() if isinstance(value, IBoolProvider) else value.AsNullableBool())