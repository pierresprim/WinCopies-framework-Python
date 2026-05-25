from abc import abstractmethod
from typing import final

from WinCopies import IInterface, Abstract
from WinCopies.Delegates import BoolFalse
from WinCopies.Typing import InvalidOperationError
from WinCopies.Typing.Delegate import Function

class IAdaptiveRefinement(IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def IsRefining(self) -> bool:
        pass
    @abstractmethod
    def IsTrueSize(self) -> bool:
        pass
    
    @final
    def GetSizeState(self) -> bool|None:
        return True if self.IsTrueSize() else (None if self.IsRefining() else False)
    
    @final
    def GetDiscoveredSize(self) -> int|None:
        low: int = self.GetLow()
        
        return None if low == 0 else low
    @final
    def TryGetDiscoveredSize(self) -> int|None:
        return self.GetLow() if self.IsTrueSize() else None
    
    @abstractmethod
    def CanSignalSuccess(self) -> bool:
        pass
    @abstractmethod
    def CanSignalError(self) -> bool:
        pass

    @abstractmethod
    def GetCurrent(self) -> int:
        pass

    @abstractmethod
    def GetLow(self) -> int:
        pass
    @abstractmethod
    def GetHigh(self) -> int|None:
        pass
    
    @abstractmethod
    def Reset(self) -> None:
        pass
    @abstractmethod
    def ResetTo(self, hint: int, refine: bool) -> None:
        pass

    @abstractmethod
    def TryOnSuccess(self) -> bool:
        pass
    @abstractmethod
    def TryOnError(self) -> bool|None:
        pass

    @final
    def OnSuccess(self) -> None:
        if not self.TryOnSuccess():
            raise InvalidOperationError()
    @final
    def OnError(self) -> None:
        if self.TryOnError() is not True:
            raise InvalidOperationError()

    @final
    def Update(self, success: bool) -> None:
        if success:
            self.OnSuccess()
        
        else:
            self.OnError()
@final
class _AdaptiveRefinement(Abstract, IAdaptiveRefinement):
    def __init__(self, current: int|None, refine: bool) -> None:
        super().__init__()

        self.__low: int = 0
        self.__high: int|None = None
        self.__delta: int = 1
        self.__current: int = 1 if current is None or current == 0 else current
        self.__refine: bool|None = refine
        self.__tryOnSuccess: Function[bool] = self.__TryOnSuccess
        self.__tryOnError: Function[bool|None] = self.__TryOnError
    
    def __AreConverged(self) -> bool:
        low: int = self.GetLow()
        high: int|None = self.GetHigh()

        if high is None or low + 1 < high:
            return False

        self.__refine = None
        self.__current = low

        self.__tryOnSuccess = BoolFalse
        self.__tryOnError = BoolFalse

        return True
    
    def __TryOnSuccess(self) -> bool:
        current: int = self.__current
        high: int|None = self.GetHigh()
        
        self.__low = current

        if high is None:
            if self.__refine:
                self.__current = 2 * current
        
        elif not self.__AreConverged():
            delta: int = 2 * self.__delta

            self.__delta = delta
            self.__current = min(self.GetLow() + delta, high - 1)
        
        return True
    def __TryOnError(self) -> bool|None:
        low: int = self.GetLow()
        current: int = self.__current

        if low == current:
            return None

        self.__refine = True

        self.__ResetDelta()
        
        self.__high = current
        
        if self.__AreConverged():
            return low > 0
        
        self.__current = low + 1
        
        return True
    
    def __ResetDelegates(self) -> None:
        self.__tryOnSuccess = self.__TryOnSuccess
        self.__tryOnError = self.__TryOnError
    def __ResetDelta(self) -> None:
        self.__delta = 1
    def __Reset(self, current: int) -> None:
        self.__ResetDelta()

        self.__current = current
    
    def CanSignalSuccess(self) -> bool:
        return not self.IsTrueSize()
    def CanSignalError(self) -> bool:
        return self.CanSignalSuccess()
    
    def GetCurrent(self) -> int:
        return self.__current
    
    def GetLow(self) -> int:
        return self.__low
    def GetHigh(self) -> int|None:
        return self.__high
    
    def TryOnSuccess(self) -> bool:
        return self.__tryOnSuccess()
    def TryOnError(self) -> bool|None:
        return self.__tryOnError()
    
    def __ResetTo(self, hint: int, refine: bool) -> None:
        self.__Reset(hint)
        self.__ResetDelegates()

        self.__low = 0
        self.__high = None
        self.__refine = refine
    
    def Reset(self) -> None:
        self.__ResetTo(1, True)
    def ResetTo(self, hint: int, refine: bool) -> None:
        if hint == 0:
            if refine:
                hint = 1
            
            else:
                raise ValueError()
        
        self.__ResetTo(hint, refine)
    
    def IsRefining(self) -> bool:
        return self.__refine is True
    
    def IsTrueSize(self) -> bool:
        return self.__refine is None

def CreateAdaptiveRefinement() -> IAdaptiveRefinement:
    return _AdaptiveRefinement(None, True)
def CreateFineRefinement(hint: int|None, refine: bool) -> IAdaptiveRefinement:
    if hint is None or hint == 0:
        if refine:
            return CreateAdaptiveRefinement()
        
        raise ValueError()
    
    if hint < 0:
        raise ValueError()
    
    return _AdaptiveRefinement(hint, refine)