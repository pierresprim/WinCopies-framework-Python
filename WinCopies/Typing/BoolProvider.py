from abc import abstractmethod, ABC
from typing import final

class IBoolProvider(ABC):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsBool(self) -> bool:
        pass

    @final
    def __bool__(self) -> bool:
        return self.AsBool()
    
    @final
    def __nonzero__(self) -> bool:
        return self.AsBool()
class IAsBool[T](IBoolProvider):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def Not(self) -> T:
        pass

class INullableBoolProvider(ABC):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsNullableBool(self) -> bool|None:
        pass

def AsBool(value: IAsBool|None) -> bool:
    return False if value is None else value.AsBool()

def AsNullableBool(value: IBoolProvider|INullableBoolProvider|None) -> bool|None:
    return None if value is None else (value.AsBool() if isinstance(value, IBoolProvider) else value.AsNullableBool())